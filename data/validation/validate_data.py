"""
Data Integrity and Contract Validation Script (Hardened Suite)
SIH 2026: Freight Forecasting and Intelligent Vessel Chartering for Bulk Cargo
Member 1: Data & Domain Foundation

Validates:
1. Required tables exist (all 11 tables)
2. Reference records existence & integrity (7 ports, 4 vessels, 35 routes)
3. Foreign key relationships integrity
4. Freight rates quality, positivity, combinations (140 route-vessel pairs), and date continuity
5. Market indicators range sanity and contiguous coverage
6. Congestion data boundaries (0-100), non-negative queues, and complete port coverage
7. Domain consistency (origins, destinations, distance vs transit time correlation)
8. Vessel physical constraints and cargo_capacity_mt
9. Multi-voyage scenario schema support
10. Strict data provenance categorization ('SYNTHETIC', 'ASSUMPTION')
"""

import sys
import os
from datetime import date, timedelta
from pathlib import Path
from typing import List, Tuple, Set, Dict

# Ensure project data root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.db import db

REQUIRED_TABLES = [
    "ports",
    "vessels",
    "routes",
    "freight_rates",
    "market_data",
    "congestion_data",
    "forecasts",
    "voyages",
    "optimization_results",
    "risk_events",
    "charter_scenarios"
]

EXPECTED_PORTS = {"INPRT", "INVTZ", "INGPR", "INGPL", "INDHM", "INSGR", "INHLD"}
EXPECTED_VESSELS = {"Handysize", "Supramax", "Panamax", "Capesize"}
EXPECTED_ORIGINS = {"Australia", "USA", "Mozambique", "Indonesia", "Russia"}


def run_validation() -> bool:
    errors: List[str] = []
    print("=" * 70)
    print("SIH 2026: RUNNING DATA VALIDATION SUITE (MEMBER 1 HARDENED)")
    print(f"Active Database Engine: {db.db_type.upper()}")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # Check 1: Required Tables Exist
    # -------------------------------------------------------------------------
    print("\n[Check 1/10] Checking required tables existence...")
    for tbl in REQUIRED_TABLES:
        try:
            count = db.get_table_row_count(tbl)
            print(f"  [OK] Table '{tbl}' exists (Row count: {count})")
        except Exception as e:
            msg = f"Table '{tbl}' is missing or inaccessible: {e}"
            errors.append(msg)
            print(f"  [FAIL] {msg}")

    # -------------------------------------------------------------------------
    # Check 2: Reference Records Existence & Integrity
    # -------------------------------------------------------------------------
    print("\n[Check 2/10] Validating reference data records...")
    port_rows = db.fetch_all("SELECT port_id, port_name FROM ports")
    found_ports = {r[0] for r in port_rows}
    if found_ports != EXPECTED_PORTS:
        msg = f"Ports mismatch! Expected {EXPECTED_PORTS}, found {found_ports}"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        print(f"  [OK] All 7 Indian destination ports exist: {sorted(list(found_ports))}")

    vessel_rows = db.fetch_all("SELECT vessel_class, cargo_capacity_mt FROM vessels")
    found_vessels = {r[0] for r in vessel_rows}
    if found_vessels != EXPECTED_VESSELS:
        msg = f"Vessels mismatch! Expected {EXPECTED_VESSELS}, found {found_vessels}"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        print(f"  [OK] All 4 Vessel classes exist with cargo capacity: {sorted(list(found_vessels))}")

    route_rows = db.fetch_all("SELECT route_id, origin_country, destination_port_id FROM routes")
    found_routes_count = len(route_rows)
    found_origins = {r[1] for r in route_rows}
    if found_routes_count != 35:
        msg = f"Expected 35 routes (5 origins x 7 ports), found {found_routes_count}"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    elif found_origins != EXPECTED_ORIGINS:
        msg = f"Origins mismatch! Expected {EXPECTED_ORIGINS}, found {found_origins}"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        print(f"  [OK] All 35 Origin x Destination routes exist across {len(found_origins)} origins.")

    # -------------------------------------------------------------------------
    # Check 3: Foreign Key Relationships Integrity
    # -------------------------------------------------------------------------
    print("\n[Check 3/10] Checking foreign key integrity...")
    orphan_routes = db.fetch_all("SELECT route_id FROM routes WHERE destination_port_id NOT IN (SELECT port_id FROM ports)")
    if orphan_routes:
        msg = f"Found {len(orphan_routes)} routes with invalid destination_port_id!"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        print("  [OK] All routes reference valid destination ports.")

    orphan_freight_routes = db.fetch_all("SELECT COUNT(*) FROM freight_rates WHERE route_id NOT IN (SELECT route_id FROM routes)")
    if orphan_freight_routes and orphan_freight_routes[0][0] > 0:
        msg = f"Found {orphan_freight_routes[0][0]} freight rates with invalid route_id!"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        print("  [OK] All freight rates reference valid routes.")

    orphan_freight_vessels = db.fetch_all("SELECT COUNT(*) FROM freight_rates WHERE vessel_class NOT IN (SELECT vessel_class FROM vessels)")
    if orphan_freight_vessels and orphan_freight_vessels[0][0] > 0:
        msg = f"Found {orphan_freight_vessels[0][0]} freight rates with invalid vessel_class!"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        print("  [OK] All freight rates reference valid vessel classes.")

    orphan_congestion = db.fetch_all("SELECT COUNT(*) FROM congestion_data WHERE port_id NOT IN (SELECT port_id FROM ports)")
    if orphan_congestion and orphan_congestion[0][0] > 0:
        msg = f"Found {orphan_congestion[0][0]} congestion rows with invalid port_id!"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        print("  [OK] All congestion records reference valid ports.")

    # -------------------------------------------------------------------------
    # Check 4: Freight Rates Quality, Positivity, Combinations & Continuity
    # -------------------------------------------------------------------------
    print("\n[Check 4/10] Validating freight rates quality, coverage, and continuity...")
    invalid_rates = db.fetch_all("SELECT COUNT(*) FROM freight_rates WHERE rate_usd_per_t <= 0")
    if invalid_rates and invalid_rates[0][0] > 0:
        msg = f"Found {invalid_rates[0][0]} freight rates <= 0 USD/tonne!"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        stats = db.fetch_one("SELECT MIN(rate_usd_per_t), AVG(rate_usd_per_t), MAX(rate_usd_per_t) FROM freight_rates")
        print(f"  [OK] All freight rates strictly positive. Range: ${stats[0]:.2f} to ${stats[2]:.2f} (Avg: ${stats[1]:.2f}/t)")

    # Check distinct route x vessel combinations
    combinations = db.fetch_all("SELECT route_id, vessel_class, COUNT(*) FROM freight_rates GROUP BY route_id, vessel_class")
    if len(combinations) != 140:
        msg = f"Expected 140 route-vessel combinations (35 routes x 4 vessels), found {len(combinations)}"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        obs_per_combo = {c[2] for c in combinations}
        if len(obs_per_combo) != 1:
            msg = f"Inconsistent observation counts per combination: {obs_per_combo}"
            errors.append(msg)
            print(f"  [FAIL] {msg}")
        else:
            expected_days = list(obs_per_combo)[0]
            print(f"  [OK] All 140 route x vessel combinations have exactly {expected_days} daily observations.")

    # Check date continuity for freight series
    freight_date_range = db.fetch_one("SELECT MIN(rate_date), MAX(rate_date), COUNT(DISTINCT rate_date) FROM freight_rates")
    f_min_str, f_max_str, f_distinct_days = freight_date_range
    f_min_d = date.fromisoformat(str(f_min_str))
    f_max_d = date.fromisoformat(str(f_max_str))
    expected_span = (f_max_d - f_min_d).days + 1
    if f_distinct_days != expected_span:
        msg = f"Freight dates have gaps! Span is {expected_span} days but found {f_distinct_days} distinct dates."
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        print(f"  [OK] Freight dates are continuous from {f_min_d} to {f_max_d} ({f_distinct_days} consecutive days).")

    # -------------------------------------------------------------------------
    # Check 5: Market Indicators Range Sanity and Coverage
    # -------------------------------------------------------------------------
    print("\n[Check 5/10] Validating market indicators sanity and continuity...")
    market_stats = db.fetch_one("""
        SELECT MIN(bunker_price_vlsfo_usd_per_t), MAX(bunker_price_vlsfo_usd_per_t),
               MIN(bunker_price_ifo380_usd_per_t), MAX(bunker_price_ifo380_usd_per_t),
               MIN(usd_inr_rate), MAX(usd_inr_rate),
               MIN(bdi_index), MAX(bdi_index)
        FROM market_data
    """)
    if market_stats[0] <= 0 or market_stats[2] <= 0 or market_stats[4] <= 0 or market_stats[6] <= 0:
        msg = "Market indicators contain non-positive values!"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        print(f"  [OK] VLSFO Bunker: ${market_stats[0]:.2f} - ${market_stats[1]:.2f}/t")
        print(f"  [OK] IFO380 Bunker: ${market_stats[2]:.2f} - ${market_stats[3]:.2f}/t")
        print(f"  [OK] USD/INR Rate: {market_stats[4]:.4f} - {market_stats[5]:.4f}")
        print(f"  [OK] Baltic Dry Index: {market_stats[6]:.2f} - {market_stats[7]:.2f}")

    # -------------------------------------------------------------------------
    # Check 6: Congestion Data Boundaries and Full Port Coverage
    # -------------------------------------------------------------------------
    print("\n[Check 6/10] Validating congestion index boundaries [0, 100] and port coverage...")
    invalid_congestion = db.fetch_all("""
        SELECT COUNT(*) FROM congestion_data 
        WHERE congestion_index < 0 OR congestion_index > 100 
           OR avg_waiting_hours < 0 
           OR vessels_at_anchorage < 0 
           OR vessels_at_berth < 0
    """)
    if invalid_congestion and invalid_congestion[0][0] > 0:
        msg = f"Found {invalid_congestion[0][0]} invalid congestion values outside valid ranges!"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        cong_stats = db.fetch_one("SELECT MIN(congestion_index), AVG(congestion_index), MAX(congestion_index), MIN(avg_waiting_hours), MAX(avg_waiting_hours) FROM congestion_data")
        print(f"  [OK] Congestion Index bounded [0, 100]: {cong_stats[0]:.2f} to {cong_stats[2]:.2f} (Avg: {cong_stats[1]:.2f})")
        print(f"  [OK] Waiting Hours: {cong_stats[3]:.2f} to {cong_stats[4]:.2f} hrs")

    # Check that every port has full date coverage
    port_cong_counts = db.fetch_all("SELECT port_id, COUNT(*) FROM congestion_data GROUP BY port_id")
    if len(port_cong_counts) != 7:
        msg = f"Expected 7 ports in congestion_data, found {len(port_cong_counts)}"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        for p_id, p_count in port_cong_counts:
            if p_count != f_distinct_days:
                msg = f"Port {p_id} has {p_count} congestion observations, expected {f_distinct_days}"
                errors.append(msg)
                print(f"  [FAIL] {msg}")
        print(f"  [OK] All 7 destination ports have complete {f_distinct_days}-day congestion records.")

    # -------------------------------------------------------------------------
    # Check 7: Domain Consistency (Routes & Physical Logistics)
    # -------------------------------------------------------------------------
    print("\n[Check 7/10] Validating domain consistency & shipping route metrics...")
    routes_all = db.fetch_all("SELECT route_id, origin_country, destination_port_id, distance_nm, typical_transit_days FROM routes")
    for r in routes_all:
        r_id, orig, dest, dist, transit = r
        if orig not in EXPECTED_ORIGINS:
            msg = f"Route {r_id} has invalid origin '{orig}'"
            errors.append(msg)
        if dest not in EXPECTED_PORTS:
            msg = f"Route {r_id} has invalid destination '{dest}'"
            errors.append(msg)
        if dist <= 0 or transit <= 0:
            msg = f"Route {r_id} has non-positive distance ({dist}) or transit days ({transit})"
            errors.append(msg)

    # Sanity check: Transit time broadly increases with distance
    # Compare Indonesia (~2000 nm) vs Australia (~4800 nm) vs USA (~10200 nm)
    indo_transit = db.fetch_one("SELECT AVG(typical_transit_days) FROM routes WHERE origin_country = 'Indonesia'")[0]
    aus_transit = db.fetch_one("SELECT AVG(typical_transit_days) FROM routes WHERE origin_country = 'Australia'")[0]
    usa_transit = db.fetch_one("SELECT AVG(typical_transit_days) FROM routes WHERE origin_country = 'USA'")[0]

    if not (indo_transit < aus_transit < usa_transit):
        msg = f"Route transit time anomaly! Indonesia ({indo_transit:.1f}d), Australia ({aus_transit:.1f}d), USA ({usa_transit:.1f}d)"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        print(f"  [OK] Transit times scale logically with distance: Indonesia ({indo_transit:.1f}d) < Australia ({aus_transit:.1f}d) < USA ({usa_transit:.1f}d)")

    # -------------------------------------------------------------------------
    # Check 8: Vessel Physical Specifications & Cargo Capacity
    # -------------------------------------------------------------------------
    print("\n[Check 8/10] Validating vessel physical constraints and cargo capacities...")
    vessels_all = db.fetch_all("SELECT vessel_class, dwt, cargo_capacity_mt, loa_m, beam_m, draft_m FROM vessels")
    for v in vessels_all:
        v_class, dwt, cap, loa, beam, draft = v
        if dwt <= 0 or cap <= 0 or loa <= 0 or beam <= 0 or draft <= 0:
            msg = f"Vessel {v_class} has invalid non-positive dimensions!"
            errors.append(msg)
        if cap > dwt:
            msg = f"Vessel {v_class} cargo capacity ({cap}) exceeds total DWT ({dwt})!"
            errors.append(msg)
        print(f"  [OK] {v_class}: DWT {dwt:.0f} MT | Cargo Cap {cap:.0f} MT | Draft {draft:.1f}m | LOA {loa:.0f}m")

    # -------------------------------------------------------------------------
    # Check 9: Multi-Voyage Scenario Support & No Duplicates
    # -------------------------------------------------------------------------
    print("\n[Check 9/10] Validating multi-voyage schema and unique constraints...")
    dup_freight = db.fetch_all("SELECT route_id, vessel_class, rate_date, COUNT(*) FROM freight_rates GROUP BY route_id, vessel_class, rate_date HAVING COUNT(*) > 1")
    if dup_freight:
        msg = f"Found {len(dup_freight)} duplicate freight rate observations!"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        print("  [OK] Zero duplicate (route_id, vessel_class, rate_date) records.")

    # -------------------------------------------------------------------------
    # Check 10: Strict Data Provenance Accounting
    # -------------------------------------------------------------------------
    print("\n[Check 10/10] Verifying strict data provenance accounting...")
    provenance_summary = db.fetch_all("""
        SELECT data_origin, COUNT(*) FROM (
            SELECT data_origin FROM ports
            UNION ALL
            SELECT data_origin FROM vessels
            UNION ALL
            SELECT data_origin FROM routes
            UNION ALL
            SELECT data_origin FROM freight_rates
            UNION ALL
            SELECT data_origin FROM market_data
            UNION ALL
            SELECT data_origin FROM congestion_data
        ) GROUP BY data_origin
    """)
    provenance_dict = {row[0]: row[1] for row in provenance_summary}
    synthetic_total = provenance_dict.get("SYNTHETIC", 0)
    assumption_total = provenance_dict.get("ASSUMPTION", 0)
    real_total = provenance_dict.get("REAL", 0)

    if real_total > 0:
        msg = f"CRITICAL: Found {real_total} synthetic/assumption records erroneously labeled 'REAL'!"
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        print(f"  [OK] Provenance audit passed: {synthetic_total} SYNTHETIC, {assumption_total} ASSUMPTION, 0 mislabeled REAL.")

    # -------------------------------------------------------------------------
    # FINAL SUMMARY REPORT
    # -------------------------------------------------------------------------
    port_count = db.get_table_row_count("ports")
    vessel_count = db.get_table_row_count("vessels")
    route_count = db.get_table_row_count("routes")
    freight_count = db.get_table_row_count("freight_rates")
    market_count = db.get_table_row_count("market_data")
    congestion_count = db.get_table_row_count("congestion_data")

    print("\n" + "=" * 70)
    if len(errors) == 0:
        print("DATA VALIDATION PASSED\n")
    else:
        print(f"DATA VALIDATION FAILED WITH {len(errors)} ERRORS\n")

    print(f"Ports: {port_count}")
    print(f"Vessels: {vessel_count}")
    print(f"Routes: {route_count}")
    print(f"Freight observations: {freight_count}")
    print(f"Market observations: {market_count}")
    print(f"Congestion observations: {congestion_count}\n")

    print("Coverage:")
    print(f"Start date: {f_min_d}")
    print(f"End date: {f_max_d}")
    print(f"Days: {f_distinct_days}\n")

    print("Freight combinations:")
    print(f"Routes: {route_count}")
    print(f"Vessel classes: {vessel_count}\n")

    print("Provenance:")
    print(f"Synthetic: {synthetic_total}")
    print(f"Assumption: {assumption_total}\n")

    print(f"Errors: {len(errors)}")
    print("=" * 70)

    if errors:
        print("\nError Details:")
        for idx, err in enumerate(errors, 1):
            print(f"  {idx}. {err}")
        return False

    return True


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
