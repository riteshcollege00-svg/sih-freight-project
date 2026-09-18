# Data Contract & Schema Specification (Hardened)

**Project:** SIH 2026 — Freight Forecasting and Intelligent Vessel Chartering for Bulk Cargo  
**Owner:** Member 1 — Data & Domain Foundation  
**Version:** 1.1.0  
**Database Engine:** PostgreSQL 16+ (with SQLite offline test-runner support)  
**Demo Timeline:** 365 days ending at `DEMO_AS_OF_DATE=2026-09-18` (Coverage: `2025-09-19` to `2026-09-18`)

---

## 1. Overview & Data Provenance Standards

All datasets in this platform strictly adhere to an auditable provenance system. Downstream systems (Member 2 Forecasting, Member 3 Optimization, Member 4 Risk & Scenarios) must preserve and verify these provenance labels.

### Permitted Data Origins (`data_origin`):
| Origin Code | Definition | Example Use Case |
| :--- | :--- | :--- |
| `REAL` | Empirically observed and verified market or AIS data | Verified historical market quotes, actual port AIS fixes |
| `SYNTHETIC` | Algorithmically generated deterministic time series (reproducible seed `42`) | 365-day freight rates, Baltic index daily simulations |
| `ASSUMPTION` | Domain-standard parameter estimates for demo/prototyping | Port maximum draft/LOA limits, vessel fuel consumption baselines |
| `MODEL_OUTPUT` | Predictions, optimal charter decisions, or simulation outputs | Member 2 Rate forecasts, Member 3 Optimization allocations |
| `SIMULATION` | Monte Carlo / stress test scenario results | Member 4 Severe weather impact / bunker spike simulations |

> **Critical Rule:** Synthetic or assumption data is **never** labeled or disguised as `REAL`.

---

## 2. Synthetic Freight Rate Generator Formula

The synthetic freight series in `freight_rates` is generated via a multi-factor structural model rather than independent random numbers. It creates realistic features suitable for evaluating time-series forecasting (Member 2) and charter timing optimization (Member 3).

### Mathematical Formulation:
$$\text{Rate}_{r, v}(t) = \text{BaseRate}_{r, v} \times \text{Trend}(t) \times \text{Seasonality}(t) \times \text{MarketCycle}_{r, v}(t) \times \text{Shock}_v(t) \times (1 + \epsilon_v(t))$$

Where:
1. **Base Rate ($\text{BaseRate}_{r, v}$):**
   $$\text{BaseRate}_{r, v} = (\text{Distance}_{r} \times 0.0036 \times \text{ScaleFactor}_v) + (10.5 \times \text{ScaleFactor}_v)$$
   * $\text{ScaleFactor}$: Capesize ($0.52$), Panamax ($0.74$), Supramax ($0.88$), Handysize ($1.05$) reflecting economies of scale.
2. **Slow Trend ($\text{Trend}(t)$):**
   $$\text{Trend}(t) = 1.0 + 0.04 \times \sin\left(\frac{t}{365} \pi\right)$$
3. **Annual Seasonality ($\text{Seasonality}(t)$):**
   $$\text{Seasonality}(t) = 1.0 + 0.12 \sin\left(\frac{2\pi (t - 30)}{365}\right) + 0.06 \sin\left(\frac{4\pi (t - 15)}{365}\right)$$
   Captures pre-monsoon Indian coal stocking surge (Apr–May), monsoon lull (Jul–Aug), and winter industrial demand recovery (Nov–Dec).
4. **Market Cycle ($\text{MarketCycle}_{r, v}(t)$):**
   $$\text{MarketCycle}_{r, v}(t) = 1.0 + 0.07 \times \text{Volatility}_v \times \sin\left(\frac{2\pi t}{75} + \phi_r\right)$$
   Represents intermediate shipping market supply-demand cycles (~75 days) with route-specific phase shift $\phi_r$.
5. **Exogenous Shocks ($\text{Shock}_v(t)$):**
   Multipliers applied during simulated weather disruptions (e.g. Australian cyclone season, canal bottlenecks, Q4 demand spikes).
6. **Stochastic Noise ($\epsilon_v(t)$):**
   $$\epsilon_v(t) \sim \mathcal{N}(0, (0.025 \times \text{Volatility}_v)^2)$$
   Generated using fixed deterministic seed (`SIMULATION_SEED=42`).

> **Disclaimer:** This synthetic dataset is constructed strictly for algorithmic demonstration, backtesting, and pipeline validation. It does **not** claim to statistically represent the actual global dry bulk freight market.

---

## 3. Detailed Table Specifications & Data Contracts

### 3.1 `ports` (Reference / Master Data)
* **Purpose:** Indian East Coast destination ports with technical berth restrictions and benchmark tariffs.
* **Primary Key:** `port_id` (`VARCHAR(32)`)
* **Data Classification:** Master Reference (`ASSUMPTION`)
* **Consumers:** Member 3 (Vessel Feasibility & Demurrage), Member 4 (Port Congestion & Cyclone Risk)

| Column | Type | Units | Valid Range | Granularity | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `port_id` | `VARCHAR(32)` | — | UN/LOCODE (e.g. `INPRT`) | Entity PK | Unique port identifier |
| `port_name` | `VARCHAR(100)`| — | Non-empty | Port | Commercial name |
| `country` | `VARCHAR(100)`| — | `'India'` | Country | Host nation |
| `coast` | `VARCHAR(50)` | — | `'East Coast India'` | Region | Coastal region |
| `latitude` | `NUMERIC(8,4)`| Degrees | $-90$ to $+90$ | Geo-coord | Latitude coordinate |
| `longitude` | `NUMERIC(8,4)`| Degrees | $-180$ to $+180$ | Geo-coord | Longitude coordinate |
| `max_draft_m` | `NUMERIC(5,2)`| **Metres (m)** | $8.50$ to $19.50$ | Physical limit | Maximum permissible arrival draft |
| `max_loa_m` | `NUMERIC(6,2)`| **Metres (m)** | $180.00$ to $320.00$ | Physical limit | Maximum permissible Length Overall |
| `max_beam_m` | `NUMERIC(5,2)`| **Metres (m)** | $28.00$ to $50.00$ | Physical limit | Maximum permissible vessel breadth |
| `handling_capacity_tpd`| `NUMERIC(10,2)`| **Tonnes/day** | $20,000$ to $80,000$ | Operational | Daily discharge throughput rate |
| `baseline_congestion_index`| `NUMERIC(5,2)`| **Index (0–100)**| $0.00$ to $100.00$ | Benchmark | Baseline congestion score |
| `avg_turnaround_days` | `NUMERIC(5,2)`| **Days** | $2.50$ to $5.00$ | Operational | Average ship turnaround time |
| `demurrage_rate_usd_day`| `NUMERIC(10,2)`| **USD/day** | $14,000$ to $20,000$ | Financial | Demurrage benchmark tariff |
| `data_origin` | `VARCHAR(20)` | — | `'ASSUMPTION'` | Provenance | Provenance classifier |

---

### 3.2 `vessels` (Reference / Master Data)
* **Purpose:** Bulk carrier class specifications, cargo carrying capacities, and consumption rates.
* **Primary Key:** `vessel_class` (`VARCHAR(50)`)
* **Data Classification:** Master Reference (`ASSUMPTION`)
* **Consumers:** Member 3 (Vessel Allocation, Draft Feasibility & Voyage Fuel Calculator)

| Column | Type | Units | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `vessel_class` | `VARCHAR(50)` | — | `Handysize`, `Supramax`, `Panamax`, `Capesize` | Bulk carrier class identifier |
| `dwt` | `NUMERIC(10,2)` | **Deadweight Tonnes (MT)** | $35,000$ to $180,000$ | Total deadweight displacement |
| `cargo_capacity_mt` | `NUMERIC(10,2)` | **Metric Tonnes (MT)** | $33,000$ to $170,000$ | Net usable cargo payload capacity |
| `loa_m` | `NUMERIC(6,2)` | **Metres (m)** | $180.00$ to $292.00$ | Length Overall |
| `beam_m` | `NUMERIC(5,2)` | **Metres (m)** | $28.00$ to $45.00$ | Extreme breadth |
| `draft_m` | `NUMERIC(5,2)` | **Metres (m)** | $10.50$ to $18.20$ | Fully-laden design draft |
| `service_speed_knots`| `NUMERIC(4,2)` | **Knots** | $12.00$ to $13.50$ | Average laden cruising speed |
| `fuel_consumption_tpd`| `NUMERIC(5,2)`| **Tonnes/day** | $22.00$ to $48.00$ | Main engine fuel consumption at sea |
| `data_origin` | `VARCHAR(20)` | — | `'ASSUMPTION'` | Provenance classifier |

---

### 3.3 `routes` (Reference Data)
* **Purpose:** 35 Origin Country × Indian Destination Port bulk coal shipping lanes.
* **Primary Key:** `route_id` (`VARCHAR(100)`)
* **Foreign Keys:** `destination_port_id` $\rightarrow$ `ports(port_id)`
* **Data Classification:** Master Reference (`ASSUMPTION`)
* **Consumers:** Member 2 (Route Segmentation), Member 3 (Voyage Transit Estimations)

| Column | Type | Units | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `route_id` | `VARCHAR(100)` | — | e.g. `RT_AUSTRALIA_PARADIP` | Route identifier |
| `origin_country` | `VARCHAR(100)` | — | Australia, USA, Mozambique, Indonesia, Russia | Export country |
| `origin_port_region` | `VARCHAR(100)` | — | Terminal region string | Load port region |
| `destination_port_id` | `VARCHAR(32)` | — | References `ports(port_id)` | Indian discharge port |
| `distance_nm` | `NUMERIC(10,2)` | **Nautical Miles (nm)** | $1,800$ to $10,500$ | Navigational distance |
| `typical_transit_days` | `NUMERIC(5,2)` | **Days** | $6.0$ to $36.0$ | Expected sailing time at service speed |
| `bunker_consumption_factor`| `NUMERIC(5,2)`| Ratio | $\ge 1.00$ | Route weather/difficulty factor |
| `data_origin` | `VARCHAR(20)` | — | `'ASSUMPTION'` | Provenance classifier |

---

### 3.4 `freight_rates` (Time Series Foundation)
* **Purpose:** Daily spot freight rates for all 140 route × vessel combinations over the configured historical window.
* **Primary Key:** `id` (`BIGSERIAL`)
* **Foreign Keys:** `route_id` $\rightarrow$ `routes(route_id)`, `vessel_class` $\rightarrow$ `vessels(vessel_class)`
* **Data Classification:** Synthetic Time Series (`SYNTHETIC`)
* **Granularity:** Daily per (route, vessel)
* **Consumers:** Member 2 (Price Forecasting Models), Member 3 (Charter Timing Engine)

| Column | Type | Units | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `BIGSERIAL` | — | Auto-increment | Row ID |
| `route_id` | `VARCHAR(100)` | — | FK $\rightarrow$ `routes` | Targeted shipping route |
| `vessel_class` | `VARCHAR(50)` | — | FK $\rightarrow$ `vessels` | Bulk vessel class |
| `rate_date` | `DATE` | — | `2025-09-19` to `2026-09-18` | Observation date |
| `rate_usd_per_t` | `NUMERIC(10,2)` | **USD per Metric Tonne ($/t)** | $> 0$ ($5.00 to $70.00/t) | Daily spot freight rate |
| `data_origin` | `VARCHAR(20)` | — | `'SYNTHETIC'` | Provenance classifier |

---

### 3.5 `market_data` (Time Series Foundation)
* **Purpose:** Daily global bunker fuel prices, currency exchange rates, and Baltic Dry index indicators.
* **Primary Key:** `id` (`BIGSERIAL`), Unique `market_date`
* **Data Classification:** Synthetic Time Series (`SYNTHETIC`)
* **Granularity:** Daily
* **Consumers:** Member 2 (Feature Engineering), Member 3 (Bunker Cost Calculation)

| Column | Type | Units | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `market_date` | `DATE` | — | `2025-09-19` to `2026-09-18` | Market observation date |
| `bunker_price_vlsfo_usd_per_t`| `NUMERIC(10,2)`| **USD/tonne** | $480.00$ to $800.00 | Very Low Sulfur Fuel Oil price |
| `bunker_price_ifo380_usd_per_t`| `NUMERIC(10,2)`| **USD/tonne** | $360.00$ to $650.00 | High Sulfur Fuel Oil (IFO 380) |
| `usd_inr_rate` | `NUMERIC(8,4)` | **INR per USD** | $82.00$ to $85.50$ | USD/INR Spot FX exchange rate |
| `bdi_index` | `NUMERIC(10,2)` | **Points** | $800$ to $3,000$ | Baltic Dry Index benchmark |
| `bci_index` | `NUMERIC(10,2)` | **Points** | $1,000$ to $5,000$ | Baltic Capesize Index |
| `bpi_index` | `NUMERIC(10,2)` | **Points** | $900$ to $2,800$ | Baltic Panamax Index |
| `bsi_index` | `NUMERIC(10,2)` | **Points** | $750$ to $2,200$ | Baltic Supramax Index |
| `bhsi_index` | `NUMERIC(10,2)` | **Points** | $500$ to $1,500$ | Baltic Handysize Index |
| `crude_oil_brent_usd` | `NUMERIC(10,2)` | **USD/bbl** | $65.00$ to $110.00$ | Brent Crude Oil benchmark |
| `data_origin` | `VARCHAR(20)` | — | `'SYNTHETIC'` | Provenance classifier |

---

### 3.6 `congestion_data` (Time Series Foundation)
* **Purpose:** Daily port-level congestion scores, anchorage queues, and waiting hours for all 7 destination ports.
* **Primary Key:** `id` (`BIGSERIAL`), Unique `(port_id, congestion_date)`
* **Foreign Keys:** `port_id` $\rightarrow$ `ports(port_id)`
* **Data Classification:** Synthetic Time Series (`SYNTHETIC`)
* **Granularity:** Daily per port
* **Consumers:** Member 3 (Demurrage Cost Calculator), Member 4 (Congestion Risk Engine)

| Column | Type | Units | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `port_id` | `VARCHAR(32)` | — | FK $\rightarrow$ `ports` | Destination Port ID |
| `congestion_date` | `DATE` | — | `2025-09-19` to `2026-09-18` | Date |
| `congestion_index` | `NUMERIC(5,2)` | **Index (0–100)** | **0.00 to 100.00** | Port Congestion Metric |
| `avg_waiting_hours`| `NUMERIC(6,2)` | **Hours (hrs)** | $\ge 0.0$ (0 to 160 hrs) | Pre-berth anchorage waiting time |
| `vessels_at_anchorage`| `INTEGER` | **Vessel count** | $\ge 0$ | Ships waiting at anchorage |
| `vessels_at_berth`| `INTEGER` | **Vessel count** | $\ge 0$ | Ships actively discharging |
| `data_origin` | `VARCHAR(20)` | — | `'SYNTHETIC'` | Provenance classifier |

---

### 3.7 `voyages` & Multi-Voyage Scenario Support (Operational Table)
* **Purpose:** Cargo movement requirements, laycan windows, and multi-voyage contract scheduling.
* **Primary Key:** `voyage_id` (`VARCHAR(100)`)
* **Foreign Keys:** 
  - `scenario_id` $\rightarrow$ `charter_scenarios(scenario_id)` (Optional FK linking voyage to a multi-voyage charter scenario)
  - `destination_port_id` $\rightarrow$ `ports(port_id)`
  - `vessel_class` $\rightarrow$ `vessels(vessel_class)`
  - `route_id` $\rightarrow$ `routes(route_id)`
* **Consumers:** Member 3 (Multi-Voyage Optimizer), Member 4 (Risk Tracking)

| Column | Type | Units | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `voyage_id` | `VARCHAR(100)` | — | Unique ID | Primary Key |
| `scenario_id` | `VARCHAR(100)` | — | FK $\rightarrow$ `charter_scenarios` | Linked simulation/charter scenario ID (Nullable) |
| `voyage_sequence` | `INTEGER` | Sequence | $\ge 1$ (e.g. 1, 2, 3...) | Order of voyage in multi-voyage program |
| `cargo_reference` | `VARCHAR(100)` | — | Lot ID | Cargo parcel identifier |
| `commodity_type` | `VARCHAR(50)` | — | Default `'Coking Coal'` | Bulk commodity |
| `origin_country` | `VARCHAR(100)` | — | Origin name | Export country |
| `destination_port_id`| `VARCHAR(32)`| — | FK $\rightarrow$ `ports` | Destination Port ID |
| `vessel_class` | `VARCHAR(50)` | — | FK $\rightarrow$ `vessels` | Chosen vessel class |
| `cargo_tonnage` | `NUMERIC(12,2)`| **Metric Tonnes (MT)**| $> 0$ | Parcel size to transport |
| `planned_laycan_start`| `DATE` | — | Date | Laycan commencement window |
| `planned_laycan_end`| `DATE` | — | $\ge \text{laycan\_start}$ | Laycan cancellation window |
| `required_delivery_date`| `DATE` | — | Date | Delivery deadline |
| `status` | `VARCHAR(50)` | — | `PLANNED`, `FIXED`, etc. | Operational lifecycle state |
| `data_origin` | `VARCHAR(20)` | — | `'ASSUMPTION'` / `'REAL'` | Provenance classifier |

---

### 3.8 `forecasts` (Populated by Member 2)
* **Purpose:** Multi-horizon out-of-sample freight rate forecasts and 95% confidence intervals across all 140 shipping route × vessel class pairs.
* **Primary Key:** `id` (`BIGSERIAL`)
* **Unique Key:** `uq_forecast_entry UNIQUE (route_id, vessel_class, forecast_generated_date, target_date, model_version)`
* **Foreign Keys:**
  - `route_id` $\rightarrow$ `routes(route_id)`
  - `vessel_class` $\rightarrow$ `vessels(vessel_class)`
* **Data Classification:** Model Outputs (`MODEL_OUTPUT`)
* **Granularity:** Row per (route, vessel, target horizon date, model)
* **Production Horizons:** 7 days, 14 days, 30 days ($35 \text{ routes} \times 4 \text{ vessels} \times 3 \text{ horizons} = \mathbf{420}\text{ records}$).
* **Consumers:** Member 3 (Intelligent Vessel Chartering & Forward Laycan Optimizer)

| Column Name | Type | Units | Valid Range | Nullable | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `BIGSERIAL` | — | Auto-increment int | No | Primary Key |
| `route_id` | `VARCHAR(100)` | — | FK $\rightarrow$ `routes` | No | Target Shipping Lane |
| `vessel_class` | `VARCHAR(50)` | — | FK $\rightarrow$ `vessels` | No | Bulk Vessel Class |
| `forecast_generated_date`| `DATE` | — | `2026-09-18` (Demo Anchor) | No | Date forecast was executed |
| `target_date` | `DATE` | — | Target future date | No | Delivery/arrival target date |
| `horizon_days` | `INTEGER` | **Days** | `7`, `14`, `30` | No | Forward forecast horizon |
| `predicted_rate_usd_per_t`| `NUMERIC(10,2)`| **USD/tonne** | $> 0$ ($5.00 - $75.00/t) | No | Out-of-sample point forecast |
| `confidence_lower_95` | `NUMERIC(10,2)`| **USD/tonne** | $> 0$ | Yes | 95% Prediction interval lower bound |
| `confidence_upper_95` | `NUMERIC(10,2)`| **USD/tonne** | $\ge \text{predicted\_rate}$| Yes | 95% Prediction interval upper bound |
| `model_version` | `VARCHAR(50)` | — | e.g. `v1.0.0`, `v1.1.0-damped` | No | Model release tag |
| `model_name` | `VARCHAR(100)` | — | Selected candidate name | No | Model architecture identifier |
| `data_origin` | `VARCHAR(20)` | — | `'MODEL_OUTPUT'` | No | Provenance label |
| `created_at` | `TIMESTAMPTZ` | — | Timestamp | No | Creation timestamp |

---

### 3.9 Charter Timing Evidence Payload Contract
Member 2 provides the reusable Python interface `get_charter_timing_evidence(route_id, vessel_class, as_of_date)`:

```json
{
  "route_id": "RT_AUSTRALIA_PARADIP",
  "vessel_class": "Capesize",
  "as_of_date": "2026-09-18",
  "current_spot_rate": 12.01,
  "median_30d": 12.07,
  "median_60d": 12.57,
  "historical_percentile": 10.8,
  "rate_velocity_7d_pct": -0.85,
  "rolling_volatility_14d": 0.42,
  "volatility_regime": "MODERATE",
  "expected_delta_14d": 0.00,
  "expected_delta_30d": 0.15,
  "confidence_spread_width": 2.15,
  "timing_evidence_signal": "NEUTRAL",
  "explanation": "The current rate ($12.01/t) is in range with the 30-day median ($12.07/t) and 60-day median ($12.57/t). The 14-day expected delta (+$0.00/t) remains within normal range-bound fluctuation boundaries under a MODERATE volatility regime.",
  "supporting_metrics": {
    "current_rate": 12.01,
    "median_30d": 12.07,
    "median_60d": 12.57,
    "historical_percentile": 10.8,
    "expected_delta_14d": 0.00,
    "expected_delta_30d": 0.15,
    "forecast_14d_point": 12.01,
    "forecast_30d_point": 12.16,
    "confidence_lower_95_14d": 10.93,
    "confidence_upper_95_14d": 13.08
  }
}
```

---

### 3.10 Downstream Remaining Contract Tables

| Table | Populated By | Primary Purpose |
| :--- | :--- | :--- |
| `optimization_results` | Member 3 | Recommended vessel allocations, charter timing, total voyage costs |
| `risk_events` | Member 4 | Registry of port/route disruptions (cyclones, swells, strikes) |
| `charter_scenarios` | Member 4 | Multi-voyage simulation scenario definitions and stress tests |
