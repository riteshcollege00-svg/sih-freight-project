"""
Reference Data Seeder
SIH 2026: Freight Forecasting and Intelligent Vessel Chartering for Bulk Cargo
Member 1: Data & Domain Foundation

Seeds core reference data:
- 7 Indian East Coast destination ports
- 4 Standard bulk vessel classes
- 35 Origin-Destination routes (5 origins x 7 destinations)
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure project data root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.db import db

# -----------------------------------------------------------------------------
# 1. PORTS REFERENCE DATA (7 Indian East Coast Ports)
# Data Origin: ASSUMPTION (Realistic demo values for SIH 2026)
# -----------------------------------------------------------------------------
PORTS_SEED: List[Dict[str, Any]] = [
    {
        "port_id": "INPRT",
        "port_name": "Paradip",
        "country": "India",
        "coast": "East Coast India",
        "latitude": 20.2644,
        "longitude": 86.6715,
        "max_draft_m": 17.10,
        "max_loa_m": 300.00,
        "max_beam_m": 48.00,
        "handling_capacity_tpd": 65000.00,
        "baseline_congestion_index": 42.00,
        "avg_turnaround_days": 3.80,
        "demurrage_rate_usd_day": 18500.00,
        "data_origin": "ASSUMPTION",
        "notes": "Major deepwater bulk port in Odisha; Capesize/Panamax coal discharge berths."
    },
    {
        "port_id": "INVTZ",
        "port_name": "Visakhapatnam",
        "country": "India",
        "coast": "East Coast India",
        "latitude": 17.6868,
        "longitude": 83.2185,
        "max_draft_m": 18.10,
        "max_loa_m": 300.00,
        "max_beam_m": 48.00,
        "handling_capacity_tpd": 70000.00,
        "baseline_congestion_index": 35.00,
        "avg_turnaround_days": 3.20,
        "demurrage_rate_usd_day": 19000.00,
        "data_origin": "ASSUMPTION",
        "notes": "Outer harbour accommodates Capesize bulk carriers; mechanized coal handling terminal."
    },
    {
        "port_id": "INGPR",
        "port_name": "Gangavaram",
        "country": "India",
        "coast": "East Coast India",
        "latitude": 17.6200,
        "longitude": 83.2350,
        "max_draft_m": 19.50,
        "max_loa_m": 320.00,
        "max_beam_m": 50.00,
        "handling_capacity_tpd": 80000.00,
        "baseline_congestion_index": 28.00,
        "avg_turnaround_days": 2.50,
        "demurrage_rate_usd_day": 20000.00,
        "data_origin": "ASSUMPTION",
        "notes": "Privately operated deep-draft port in Andhra Pradesh; handles fully-laden Capesize vessels."
    },
    {
        "port_id": "INGPL",
        "port_name": "Gopalpur",
        "country": "India",
        "coast": "East Coast India",
        "latitude": 19.3000,
        "longitude": 84.9667,
        "max_draft_m": 13.00,
        "max_loa_m": 225.00,
        "max_beam_m": 33.00,
        "handling_capacity_tpd": 25000.00,
        "baseline_congestion_index": 20.00,
        "avg_turnaround_days": 2.80,
        "demurrage_rate_usd_day": 15000.00,
        "data_origin": "ASSUMPTION",
        "notes": "All-weather commercial port in southern Odisha; suitable for Handysize and Supramax."
    },
    {
        "port_id": "INDHM",
        "port_name": "Dhamra",
        "country": "India",
        "coast": "East Coast India",
        "latitude": 20.8250,
        "longitude": 86.9650,
        "max_draft_m": 18.50,
        "max_loa_m": 300.00,
        "max_beam_m": 48.00,
        "handling_capacity_tpd": 75000.00,
        "baseline_congestion_index": 30.00,
        "avg_turnaround_days": 2.60,
        "demurrage_rate_usd_day": 19500.00,
        "data_origin": "ASSUMPTION",
        "notes": "Modern deepwater port north of Dhamra river; highly automated Capesize coal berths."
    },
    {
        "port_id": "INSGR",
        "port_name": "Sagar/Sandheads",
        "country": "India",
        "coast": "East Coast India",
        "latitude": 21.6500,
        "longitude": 88.0500,
        "max_draft_m": 11.50,
        "max_loa_m": 200.00,
        "max_beam_m": 30.00,
        "handling_capacity_tpd": 20000.00,
        "baseline_congestion_index": 48.00,
        "avg_turnaround_days": 4.50,
        "demurrage_rate_usd_day": 14000.00,
        "data_origin": "ASSUMPTION",
        "notes": "Transshipment / lighterage anchorage and deep draft river approach."
    },
    {
        "port_id": "INHLD",
        "port_name": "Haldia",
        "country": "India",
        "coast": "East Coast India",
        "latitude": 22.0200,
        "longitude": 88.0600,
        "max_draft_m": 8.50,
        "max_loa_m": 190.00,
        "max_beam_m": 29.00,
        "handling_capacity_tpd": 22000.00,
        "baseline_congestion_index": 55.00,
        "avg_turnaround_days": 4.90,
        "demurrage_rate_usd_day": 14500.00,
        "data_origin": "ASSUMPTION",
        "notes": "Riverine dock system subject to draft restrictions and tidal navigation constraints."
    }
]

# -----------------------------------------------------------------------------
# 2. VESSELS REFERENCE DATA (4 Standard Dry Bulk Carrier Classes)
# Data Origin: ASSUMPTION (Standard commercial dry bulk parameters)
# -----------------------------------------------------------------------------
VESSELS_SEED: List[Dict[str, Any]] = [
    {
        "vessel_class": "Handysize",
        "dwt": 35000.00,
        "cargo_capacity_mt": 33000.00,
        "loa_m": 180.00,
        "beam_m": 28.00,
        "draft_m": 10.50,
        "service_speed_knots": 12.00,
        "fuel_consumption_tpd": 22.00,
        "data_origin": "ASSUMPTION",
        "notes": "Geared bulk carrier; versatile access to draft-restricted ports like Haldia & Sagar."
    },
    {
        "vessel_class": "Supramax",
        "dwt": 58000.00,
        "cargo_capacity_mt": 55000.00,
        "loa_m": 190.00,
        "beam_m": 32.00,
        "draft_m": 12.00,
        "service_speed_knots": 12.50,
        "fuel_consumption_tpd": 28.00,
        "data_origin": "ASSUMPTION",
        "notes": "Geared vessel with grabs; flexible parcel sizes for regional coal logistics."
    },
    {
        "vessel_class": "Panamax",
        "dwt": 82000.00,
        "cargo_capacity_mt": 78000.00,
        "loa_m": 225.00,
        "beam_m": 32.30,
        "draft_m": 14.20,
        "service_speed_knots": 13.00,
        "fuel_consumption_tpd": 33.00,
        "data_origin": "ASSUMPTION",
        "notes": "Gearless bulk carrier; primary workhorse for standard Indian coal imports."
    },
    {
        "vessel_class": "Capesize",
        "dwt": 180000.00,
        "cargo_capacity_mt": 170000.00,
        "loa_m": 292.00,
        "beam_m": 45.00,
        "draft_m": 18.20,
        "service_speed_knots": 13.50,
        "fuel_consumption_tpd": 48.00,
        "data_origin": "ASSUMPTION",
        "notes": "Large bulk carrier for high-volume coal routes (Australia/USA) to deepwater ports."
    }
]

# -----------------------------------------------------------------------------
# 3. ORIGIN REGIONS
# -----------------------------------------------------------------------------
ORIGIN_REGIONS: List[Dict[str, Any]] = [
    {
        "country": "Australia",
        "region": "Hay Point / Gladstone (Queensland)",
        "base_distance_nm": 4800.00
    },
    {
        "country": "USA",
        "region": "Hampton Roads / US Gulf",
        "base_distance_nm": 10200.00
    },
    {
        "country": "Mozambique",
        "region": "Maputo / Beira",
        "base_distance_nm": 4100.00
    },
    {
        "country": "Indonesia",
        "region": "Taboneo / Balikpapan (Kalimantan)",
        "base_distance_nm": 2100.00
    },
    {
        "country": "Russia",
        "region": "Taman (Black Sea) / Vostochny (Far East)",
        "base_distance_nm": 6400.00
    }
]

# Port distance adjustment offsets (nautical miles relative to central Bay of Bengal waypoint)
PORT_DISTANCE_OFFSETS = {
    "INVTZ": -120.0,   # Visakhapatnam (southernmost of major cluster)
    "INGPR": -125.0,   # Gangavaram (adjacent to Vizag)
    "INGPL": -40.0,    # Gopalpur
    "INPRT": 0.0,      # Paradip (baseline reference)
    "INDHM": +35.0,    # Dhamra (north of Paradip)
    "INSGR": +140.0,   # Sagar (river mouth)
    "INHLD": +185.0    # Haldia (upstream river port)
}


def generate_routes() -> List[Dict[str, Any]]:
    """Generates 35 coherent Origin x Destination routes with nautical distances & transit days."""
    routes = []
    average_speed_knots = 12.50

    for origin in ORIGIN_REGIONS:
        for port in PORTS_SEED:
            port_id = port["port_id"]
            port_name = port["port_name"]
            country_clean = origin["country"].upper().replace(" ", "_")
            port_clean = port_name.upper().replace(" ", "_").replace("/", "_")
            route_id = f"RT_{country_clean}_{port_clean}"

            offset = PORT_DISTANCE_OFFSETS.get(port_id, 0.0)
            distance_nm = round(origin["base_distance_nm"] + offset, 2)
            # Transit days = distance / (speed * 24) + small buffer (0.5 day for canal/pilotage)
            transit_days = round((distance_nm / (average_speed_knots * 24.0)) + 0.5, 2)

            routes.append({
                "route_id": route_id,
                "origin_country": origin["country"],
                "origin_port_region": origin["region"],
                "destination_port_id": port_id,
                "distance_nm": distance_nm,
                "typical_transit_days": transit_days,
                "bunker_consumption_factor": 1.00,
                "data_origin": "ASSUMPTION",
                "notes": f"Standard bulk coal shipping lane from {origin['region']} to {port_name}, India."
            })
    return routes


def seed_all_reference_data():
    """Initializes schema and seeds all reference tables."""
    print("=" * 70)
    print("SIH 2026: SEEDING REFERENCE DATA (MEMBER 1)")
    print(f"Target Database Type: {db.db_type.upper()}")
    print("=" * 70)

    # 1. Initialize schema
    print("\n[1/4] Applying initial schema DDL...")
    db.init_schema()
    print("Schema initialized successfully.")

    # 2. Seed Ports
    print(f"\n[2/4] Seeding {len(PORTS_SEED)} Indian Destination Ports...")
    port_query = """
        INSERT INTO ports (
            port_id, port_name, country, coast, latitude, longitude,
            max_draft_m, max_loa_m, max_beam_m, handling_capacity_tpd,
            baseline_congestion_index, avg_turnaround_days, demurrage_rate_usd_day,
            data_origin, notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    port_params = [
        (
            p["port_id"], p["port_name"], p["country"], p["coast"],
            p["latitude"], p["longitude"], p["max_draft_m"], p["max_loa_m"],
            p["max_beam_m"], p["handling_capacity_tpd"], p["baseline_congestion_index"],
            p["avg_turnaround_days"], p["demurrage_rate_usd_day"], p["data_origin"], p["notes"]
        )
        for p in PORTS_SEED
    ]
    db.execute_many(port_query, port_params)
    print(f"-> Successfully inserted {len(PORTS_SEED)} ports.")

    # 3. Seed Vessels
    print(f"\n[3/4] Seeding {len(VESSELS_SEED)} Dry Bulk Vessel Classes...")
    vessel_query = """
        INSERT INTO vessels (
            vessel_class, dwt, cargo_capacity_mt, loa_m, beam_m, draft_m,
            service_speed_knots, fuel_consumption_tpd, data_origin, notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    vessel_params = [
        (
            v["vessel_class"], v["dwt"], v["cargo_capacity_mt"], v["loa_m"], v["beam_m"], v["draft_m"],
            v["service_speed_knots"], v["fuel_consumption_tpd"], v["data_origin"], v["notes"]
        )
        for v in VESSELS_SEED
    ]
    db.execute_many(vessel_query, vessel_params)
    print(f"-> Successfully inserted {len(VESSELS_SEED)} vessel classes.")

    # 4. Seed Routes
    routes = generate_routes()
    print(f"\n[4/4] Seeding {len(routes)} Origin-to-Destination Shipping Routes...")
    route_query = """
        INSERT INTO routes (
            route_id, origin_country, origin_port_region, destination_port_id,
            distance_nm, typical_transit_days, bunker_consumption_factor, data_origin, notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    route_params = [
        (
            r["route_id"], r["origin_country"], r["origin_port_region"], r["destination_port_id"],
            r["distance_nm"], r["typical_transit_days"], r["bunker_consumption_factor"],
            r["data_origin"], r["notes"]
        )
        for r in routes
    ]
    db.execute_many(route_query, route_params)
    print(f"-> Successfully inserted {len(routes)} shipping routes.")

    print("\nReference data seeding complete.")
    print("=" * 70)


if __name__ == "__main__":
    seed_all_reference_data()
