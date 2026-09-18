# SIH 2026: Member 1 — Data & Domain Foundation (Hardened)

**Project:** Freight Forecasting and Intelligent Vessel Chartering for Bulk Cargo  
**Role Ownership:** Database schema, reference master data, deterministic synthetic data generators, data provenance, validation test suite, and team data contracts.

---

## 🚀 Quick Start & Demo Timeline

The demonstration scenario uses an active demo as-of date in **2026**:
* **Demo As-Of Date (`DEMO_AS_OF_DATE`):** `2026-09-18` (configurable in `.env`)
* **Historical Window (`DATA_HISTORY_DAYS`):** `365` days (Coverage: `2025-09-19` to `2026-09-18`)
* **Simulation Seed (`SIMULATION_SEED`):** `42` (strictly reproducible)

### 1. Start PostgreSQL with Docker Compose
If Docker is installed:
```bash
docker compose up -d
```
*Note: If Docker is unavailable, python scripts automatically use an isolated local SQLite fallback (`data/freight_chartering_demo.db`).*

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Full Data Pipeline (Seed -> Generate -> Validate)
```bash
# Step 1: Initialize schema and seed reference data (Ports, Vessels with cargo capacities, Routes)
python data/seed/seed_reference_data.py

# Step 2: Generate 365-day deterministic synthetic time series (Freight, Market, Congestion)
python data/generators/generate_demo_data.py

# Step 3: Run full integrity and data-contract validation
python data/validation/validate_data.py
```

Expected validation output:
```text
======================================================================
DATA VALIDATION PASSED

Ports: 7
Vessels: 4
Routes: 35
Freight observations: 51100
Market observations: 365
Congestion observations: 2555

Coverage:
Start date: 2025-09-19
End date: 2026-09-18
Days: 365

Freight combinations:
Routes: 35
Vessel classes: 4

Provenance:
Synthetic: 54020
Assumption: 46

Errors: 0
======================================================================
```

---

## 📁 Repository Structure

```text
/data
  ├── db.py                          # Database manager (PostgreSQL 16+ with SQLite test runner)
  ├── README.md                      # This documentation guide
  ├── schema/
  │   └── 001_initial_schema.sql     # PostgreSQL 16+ DDL for all 11 core tables
  ├── seed/
  │   └── seed_reference_data.py     # Master data seeder (7 ports, 4 vessels, 35 routes)
  ├── generators/
  │   └── generate_demo_data.py      # Deterministic generator (Freight, Market, Congestion)
  ├── validation/
  │   └── validate_data.py           # Contract and integrity validation suite
  └── docs/
      └── DATA_CONTRACT.md           # Formal specification, generator formula, and units contract
```

---

## 📊 Summary of Core Tables

| Table | Records | Provenance | Description | Primary Consumer |
| :--- | :---: | :--- | :--- | :--- |
| `ports` | 7 | `ASSUMPTION` | Indian East Coast ports with max draft/LOA limits | Member 3 & 4 |
| `vessels` | 4 | `ASSUMPTION` | Handysize, Supramax, Panamax, Capesize + `cargo_capacity_mt` | Member 3 |
| `routes` | 35 | `ASSUMPTION` | 5 Origins × 7 Indian Ports shipping lanes & distances | Member 2 & 3 |
| `freight_rates` | 51,100 | `SYNTHETIC` | 365-day daily spot rates across 140 route-vessel pairs | Member 2 (Forecasting) |
| `market_data` | 365 | `SYNTHETIC` | Daily VLSFO/IFO380 bunker fuel, USD/INR, Baltic Indices | Member 2 & 3 |
| `congestion_data`| 2,555 | `SYNTHETIC` | Daily port congestion index (0-100), waiting hours | Member 3 & 4 |
| `voyages` | Schema | `ASSUMPTION` | Multi-voyage program with `scenario_id` & `voyage_sequence` | Member 3 & 4 |
| `forecasts` | Schema | `MODEL_OUTPUT` | Reserved for Member 2 forecasting model outputs | Member 2 |
| `optimization_results` | Schema | `MODEL_OUTPUT` | Reserved for Member 3 vessel allocation recommendations | Member 3 |
| `risk_events` | Schema | `SIMULATION` | Reserved for Member 4 disruption registry | Member 4 |
| `charter_scenarios` | Schema | `SIMULATION` | Reserved for Member 4 scenario definitions | Member 4 |

---

## 👥 Downstream Team Member Consumption Guide

### For Member 2 (Freight Forecasting Models)
* **Tables to Read:** `freight_rates`, `market_data`, `routes`, `vessels`
* **Table to Populate:** `forecasts`
* **Historical Timeline:** Spans `2025-09-19` to `2026-09-18` (365 consecutive days).
* **Generator Formula Details:** See [DATA_CONTRACT.md](file:///c:/Projects/SIH/data/docs/DATA_CONTRACT.md#2-synthetic-freight-rate-generator-formula).

### For Member 3 (Vessel Allocation & Optimization Engine)
* **Tables to Read:** `ports`, `vessels`, `routes`, `forecasts`, `congestion_data`, `market_data`, `voyages`
* **Table to Populate:** `optimization_results`
* **Multi-Voyage Support:** The `voyages` table supports `scenario_id` and `voyage_sequence` to link sequential voyages within a multi-voyage charter program.

### For Member 4 (Risk Scoring & Scenario Engine)
* **Tables to Read:** `congestion_data`, `ports`, `routes`, `market_data`, `optimization_results`
* **Tables to Populate:** `risk_events`, `charter_scenarios`

---

## 🧪 Running Unit & Integration Tests
Execute the automated test suite anytime:
```bash
python tests/test_data_foundation.py
```
This validates all 10 integrity, determinism, physical constraint, and contract requirements.
