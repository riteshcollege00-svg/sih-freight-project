"""
Deterministic Synthetic Demo Data Generator
SIH 2026: Freight Forecasting and Intelligent Vessel Chartering for Bulk Cargo
Member 1: Data & Domain Foundation

Generates:
- 365 days of daily Freight Rates across 35 routes x 4 vessel classes (51,100 records)
- 365 days of daily Market Indicators (Bunker prices, USD/INR, Baltic Dry Indices)
- 365 days of Port Congestion Data across 7 Indian destination ports (2,555 records)

Strictly deterministic: Uses fixed random seed (42) for 100% reproducibility.
Data Origin: 'SYNTHETIC'
"""

import os
import sys
import math
import random
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

# Ensure project data root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.db import db

# Configuration with fallback support
def get_config_params(
    as_of_date: Optional[date] = None,
    history_days: Optional[int] = None,
    seed: Optional[int] = None
) -> Tuple[date, date, int, int]:
    """Resolves demo timeline, history length, and seed configuration."""
    resolved_seed = seed
    if resolved_seed is None:
        resolved_seed = int(os.getenv("SIMULATION_SEED", os.getenv("RANDOM_SEED", "42")))

    resolved_days = history_days
    if resolved_days is None:
        resolved_days = int(os.getenv("DATA_HISTORY_DAYS", os.getenv("SIMULATION_DAYS", "365")))

    resolved_end_date = as_of_date
    if resolved_end_date is None:
        as_of_str = os.getenv("DEMO_AS_OF_DATE", "2026-09-18")
        resolved_end_date = date.fromisoformat(as_of_str)

    resolved_start_date = resolved_end_date - timedelta(days=resolved_days - 1)
    return resolved_start_date, resolved_end_date, resolved_days, resolved_seed


DEFAULT_START_DATE, DEFAULT_END_DATE, DEFAULT_HISTORY_DAYS, DEFAULT_SEED = get_config_params()


# -----------------------------------------------------------------------------
# DETERMINISTIC FREIGHT RATE GENERATOR
# -----------------------------------------------------------------------------

# Vessel class economies of scale factor (Capesize has lowest USD/tonne freight cost, Handysize highest)
VESSEL_SCALE_FACTORS = {
    "Capesize": 0.52,
    "Panamax": 0.74,
    "Supramax": 0.88,
    "Handysize": 1.05
}

# Vessel class market volatility multiplier (Capesize is high beta / volatile; Handysize is low beta)
VESSEL_VOLATILITY = {
    "Capesize": 1.70,
    "Panamax": 1.25,
    "Supramax": 1.00,
    "Handysize": 0.80
}


def generate_freight_rates_data(
    as_of_date: Optional[date] = None,
    history_days: Optional[int] = None,
    seed: Optional[int] = None
) -> List[Tuple]:
    """
    Generates deterministic freight rates for each route x vessel_class combination.
    Each series incorporates:
    1. Base rate (distance + vessel scale economy)
    2. Slow macro trend
    3. Annual seasonality (pre-monsoon coal stockpiling peak, monsoon lull, Q4 surge)
    4. Medium-term market cycle waves (~60-90 day shipping cycles)
    5. Exogenous market shock events (weather anomalies, canal delays, supply crunches)
    6. Reproducible pseudo-random noise
    """
    start_date, end_date, total_days, resolved_seed = get_config_params(as_of_date, history_days, seed)
    rng = random.Random(resolved_seed)

    # Fetch all routes and vessels from DB
    routes = db.fetch_all("SELECT route_id, distance_nm, origin_country, destination_port_id FROM routes ORDER BY route_id")
    vessels = db.fetch_all("SELECT vessel_class, dwt FROM vessels ORDER BY dwt")

    records = []

    # Pre-generate macro shock calendar (day index -> shock magnitude)
    shocks = {
        45: 1.18, 46: 1.22, 47: 1.20, 48: 1.15, 49: 1.08,
        160: 1.14, 161: 1.16, 162: 1.15, 163: 1.10,
        280: 1.25, 281: 1.28, 282: 1.24, 283: 1.18, 284: 1.10,
        340: 0.88, 341: 0.86, 342: 0.87 # Year-end holiday slump
    }

    for route in routes:
        route_id, distance_nm, origin, dest = route
        dist = float(distance_nm)

        for vessel in vessels:
            v_class, dwt = vessel
            scale_factor = VESSEL_SCALE_FACTORS.get(v_class, 0.80)
            volatility = VESSEL_VOLATILITY.get(v_class, 1.00)

            # Base cost per nautical mile per ton: ~$0.0036/nm + handling base
            base_rate = (dist * 0.0036 * scale_factor) + (10.5 * scale_factor)

            # Route-specific phase shift so routes don't move in exact lockstep
            route_phase = (hash(route_id) % 100) / 100.0 * 2 * math.pi

            for day_idx in range(total_days):
                current_date = start_date + timedelta(days=day_idx)

                # 1. Slow annual trend (-3% to +5% gentle structural drift)
                trend = 1.0 + (0.04 * math.sin((day_idx / 365.0) * math.pi))

                # 2. Seasonality (Pre-monsoon stocking Q2 peak around day 110-140, monsoon dip in July/Aug day 180-230, Q4 surge day 290-330)
                seasonality = 1.0 + 0.12 * math.sin((2 * math.pi * (day_idx - 30)) / 365.0) \
                                  + 0.06 * math.sin((4 * math.pi * (day_idx - 15)) / 365.0)

                # 3. Market cycle (~75 day medium-frequency chartering cycle)
                market_cycle = 1.0 + (0.07 * volatility * math.sin(((2 * math.pi * day_idx) / 75.0) + route_phase))

                # 4. Shock multiplier
                shock = shocks.get(day_idx % 365, 1.0)
                if shock > 1.0:
                    shock = 1.0 + ((shock - 1.0) * volatility)
                elif shock < 1.0:
                    shock = 1.0 - ((1.0 - shock) * volatility)

                # 5. Gaussian noise
                noise = rng.gauss(0.0, 0.025 * volatility)

                # Combine all factors
                rate = base_rate * trend * seasonality * market_cycle * shock * (1.0 + noise)

                # Enforce safety minimum (freight rate must always be positive)
                rate = max(round(rate, 2), 4.50)

                records.append((
                    route_id,
                    v_class,
                    current_date,
                    rate,
                    "SYNTHETIC"
                ))

    return records


# -----------------------------------------------------------------------------
# DETERMINISTIC MARKET DATA GENERATOR
# -----------------------------------------------------------------------------

def generate_market_data(
    as_of_date: Optional[date] = None,
    history_days: Optional[int] = None,
    seed: Optional[int] = None
) -> List[Tuple]:
    """
    Generates deterministic global market indicators:
    - VLSFO Bunker Fuel ($/t)
    - IFO380 Bunker Fuel ($/t)
    - USD/INR FX Rate
    - Baltic Dry Index (BDI) and component sub-indices (BCI, BPI, BSI, BHSI)
    - Brent Crude Oil ($/bbl)
    """
    start_date, end_date, total_days, resolved_seed = get_config_params(as_of_date, history_days, seed)
    rng = random.Random(resolved_seed + 100)
    records = []

    # Initial starting states
    vlsfo_base = 635.0
    ifo380_base = 475.0
    usd_inr_base = 83.10
    brent_base = 82.50
    bdi_base = 1580.0

    for day_idx in range(total_days):
        current_date = start_date + timedelta(days=day_idx)

        # Macro annual drift
        macro_t = day_idx / 365.0

        # Oil & Bunker evolution
        oil_cycle = 6.0 * math.sin((2 * math.pi * day_idx) / 180.0)
        oil_noise = rng.gauss(0, 0.8)
        brent = round(max(brent_base + (macro_t * 4.0) + oil_cycle + oil_noise, 65.0), 2)

        # Bunker prices track crude oil with refinery crack spread
        vlsfo_spread = 540.0 + (brent * 1.35) + rng.gauss(0, 4.0)
        vlsfo = round(max(vlsfo_spread, 480.0), 2)

        ifo_spread = 380.0 + (brent * 1.10) + rng.gauss(0, 3.5)
        ifo380 = round(max(ifo_spread, 360.0), 2)

        # USD/INR slight steady depreciation drift over the year + small noise
        usd_inr = round(usd_inr_base + (macro_t * 1.15) + (rng.gauss(0, 0.04)), 4)

        # Baltic Dry Index (BDI) and sub-indices
        bdi_season = 250.0 * math.sin((2 * math.pi * (day_idx - 40)) / 365.0)
        bdi_cycle = 180.0 * math.cos((2 * math.pi * day_idx) / 80.0)
        bdi_noise = rng.gauss(0, 35.0)
        bdi = round(max(bdi_base + (macro_t * 120.0) + bdi_season + bdi_cycle + bdi_noise, 850.0), 2)

        # Sub-indices anchored to BDI with class-specific betas
        bci = round(max((bdi * 1.45) + rng.gauss(0, 60.0), 1000.0), 2)   # Capesize Index
        bpi = round(max((bdi * 1.05) + rng.gauss(0, 30.0), 900.0), 2)    # Panamax Index
        bsi = round(max((bdi * 0.88) + rng.gauss(0, 20.0), 750.0), 2)    # Supramax Index
        bhsi = round(max((bdi * 0.60) + rng.gauss(0, 15.0), 500.0), 2)   # Handysize Index

        records.append((
            current_date,
            vlsfo,
            ifo380,
            usd_inr,
            bdi,
            bci,
            bpi,
            bsi,
            bhsi,
            brent,
            "SYNTHETIC"
        ))

    return records


# -----------------------------------------------------------------------------
# DETERMINISTIC CONGESTION DATA GENERATOR
# -----------------------------------------------------------------------------

def generate_congestion_data(
    as_of_date: Optional[date] = None,
    history_days: Optional[int] = None,
    seed: Optional[int] = None
) -> List[Tuple]:
    """
    Generates daily Congestion Data across 7 Indian destination ports.
    Includes:
    - Port baseline congestion
    - Monsoon weather surge (June to August)
    - Pre-monsoon / festival vessel arrival surges
    - Port-specific occasional congestion spikes
    - Bounded congestion index [0, 100]
    - Realistic anchorage / berth queue counts
    """
    start_date, end_date, total_days, resolved_seed = get_config_params(as_of_date, history_days, seed)

    ports = db.fetch_all("SELECT port_id, baseline_congestion_index, avg_turnaround_days FROM ports ORDER BY port_id")
    records = []

    for port in ports:
        port_id, baseline_idx, avg_turnaround = port
        base_cong = float(baseline_idx)
        turnaround = float(avg_turnaround)

        port_rng = random.Random(resolved_seed + hash(port_id) % 10000)

        for day_idx in range(total_days):
            current_date = start_date + timedelta(days=day_idx)

            # 1. Monsoon effect on East Coast (days 150 to 240: June to August swell)
            monsoon_surge = 0.0
            if 150 <= (day_idx % 365) <= 240:
                monsoon_surge = 14.0 * math.sin((((day_idx % 365) - 150) / 90.0) * math.pi)

            # 2. Pre-monsoon arrival clustering (days 90 to 140: April to May)
            stockpile_surge = 0.0
            if 90 <= (day_idx % 365) <= 140:
                stockpile_surge = 8.0 * math.sin((((day_idx % 365) - 90) / 50.0) * math.pi)

            # 3. Slow multi-week wave
            slow_wave = 5.0 * math.sin((2 * math.pi * day_idx) / 45.0)

            # 4. Occasional random queue spike
            spike = 0.0
            if port_rng.random() < 0.035:
                spike = port_rng.uniform(12.0, 26.0)

            # 5. Daily variation noise
            noise = port_rng.gauss(0, 2.5)

            # Total congestion index clamped strictly between [0.00, 100.00]
            congestion_idx = base_cong + monsoon_surge + stockpile_surge + slow_wave + spike + noise
            congestion_idx = round(max(0.0, min(100.0, congestion_idx)), 2)

            # Waiting hours roughly scales with congestion index and port turnaround
            avg_waiting_hours = round(max(0.0, (congestion_idx / 100.0) * (turnaround * 24.0 * 1.3) + port_rng.gauss(0, 2.0)), 2)

            # Vessels queue estimation
            vessels_at_anchorage = max(0, int((congestion_idx / 100.0) * 14 + port_rng.randint(-1, 2)))
            vessels_at_berth = max(1, int((base_cong / 20.0) + port_rng.randint(0, 2)))

            records.append((
                port_id,
                current_date,
                congestion_idx,
                avg_waiting_hours,
                vessels_at_anchorage,
                vessels_at_berth,
                "SYNTHETIC"
            ))

    return records


# -----------------------------------------------------------------------------
# MAIN ORCHESTRATION FUNCTION
# -----------------------------------------------------------------------------

def generate_and_load_demo_data(
    as_of_date: Optional[date] = None,
    history_days: Optional[int] = None,
    seed: Optional[int] = None
):
    """Generates and inserts all synthetic demo data into the database."""
    start_date, end_date, total_days, resolved_seed = get_config_params(as_of_date, history_days, seed)

    print("=" * 70)
    print("SIH 2026: GENERATING DETERMINISTIC SYNTHETIC DATA (MEMBER 1)")
    print(f"Random Seed: {resolved_seed} | Period: {start_date} to {end_date} ({total_days} days)")
    print(f"Target Database Type: {db.db_type.upper()}")
    print("=" * 70)

    # 1. Market Data
    print("\n[1/3] Generating daily global market indicators...")
    market_records = generate_market_data(as_of_date, history_days, seed)
    market_query = """
        INSERT INTO market_data (
            market_date, bunker_price_vlsfo_usd_per_t, bunker_price_ifo380_usd_per_t,
            usd_inr_rate, bdi_index, bci_index, bpi_index, bsi_index, bhsi_index,
            crude_oil_brent_usd, data_origin
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    db.execute_many(market_query, market_records)
    print(f"-> Successfully inserted {len(market_records)} daily market records.")

    # 2. Congestion Data
    print("\n[2/3] Generating port congestion observations...")
    congestion_records = generate_congestion_data(as_of_date, history_days, seed)
    congestion_query = """
        INSERT INTO congestion_data (
            port_id, congestion_date, congestion_index, avg_waiting_hours,
            vessels_at_anchorage, vessels_at_berth, data_origin
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    db.execute_many(congestion_query, congestion_records)
    print(f"-> Successfully inserted {len(congestion_records)} port congestion records.")

    # 3. Freight Rates Data
    print("\n[3/3] Generating historical freight rate observations across all routes & vessels...")
    freight_records = generate_freight_rates_data(as_of_date, history_days, seed)
    freight_query = """
        INSERT INTO freight_rates (
            route_id, vessel_class, rate_date, rate_usd_per_t, data_origin
        ) VALUES (%s, %s, %s, %s, %s)
    """
    db.execute_many(freight_query, freight_records)
    print(f"-> Successfully inserted {len(freight_records)} freight rate records.")

    print("\nDemo data generation and database population completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    generate_and_load_demo_data()
