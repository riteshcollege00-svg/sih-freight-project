"""
Unit and Integration Tests for Member 1 Data Foundation (Hardened Test Suite)
SIH 2026: Freight Forecasting and Intelligent Vessel Chartering for Bulk Cargo
"""

import os
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.db import db
from data.seed.seed_reference_data import seed_all_reference_data, PORTS_SEED, VESSELS_SEED
from data.generators.generate_demo_data import (
    generate_and_load_demo_data,
    generate_freight_rates_data,
    generate_market_data,
    generate_congestion_data,
    get_config_params
)
from data.validation.validate_data import run_validation


class TestDataFoundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Seed and generate test data with default 2026 demo timeline
        seed_all_reference_data()
        generate_and_load_demo_data()

    def test_01_all_11_tables_exist(self):
        expected_tables = [
            "ports", "vessels", "routes", "freight_rates", "market_data",
            "congestion_data", "forecasts", "voyages", "optimization_results",
            "risk_events", "charter_scenarios"
        ]
        for tbl in expected_tables:
            count = db.get_table_row_count(tbl)
            self.assertIsNotNone(count, f"Table {tbl} should exist")

    def test_02_ports_count_and_provenance(self):
        ports = db.fetch_all("SELECT port_id, data_origin, max_draft_m, max_loa_m FROM ports")
        self.assertEqual(len(ports), 7, "Must have exactly 7 Indian ports")
        for port_id, origin, draft, loa in ports:
            self.assertEqual(origin, "ASSUMPTION", "Port reference data origin must be ASSUMPTION")
            self.assertGreater(draft, 0)
            self.assertGreater(loa, 0)

    def test_03_vessels_count_and_cargo_capacity(self):
        vessels = db.fetch_all("SELECT vessel_class, dwt, cargo_capacity_mt, loa_m, beam_m, draft_m, data_origin FROM vessels")
        self.assertEqual(len(vessels), 4, "Must have exactly 4 vessel classes")
        for v_class, dwt, cap, loa, beam, draft, origin in vessels:
            self.assertGreater(dwt, 0)
            self.assertGreater(cap, 0, "cargo_capacity_mt must be strictly positive")
            self.assertLessEqual(cap, dwt, "cargo_capacity_mt cannot exceed total dwt")
            self.assertGreater(loa, 0)
            self.assertGreater(beam, 0)
            self.assertGreater(draft, 0)
            self.assertEqual(origin, "ASSUMPTION")

    def test_04_routes_count_and_distance_scaling(self):
        routes = db.fetch_all("SELECT route_id, origin_country, distance_nm, typical_transit_days FROM routes")
        self.assertEqual(len(routes), 35, "Must have 35 routes (5 origins x 7 ports)")
        origins = {r[1] for r in routes}
        self.assertEqual(origins, {"Australia", "USA", "Mozambique", "Indonesia", "Russia"})
        for r_id, orig, dist, transit in routes:
            self.assertGreater(dist, 0)
            self.assertGreater(transit, 0)

        # Transit time scaling check
        indo_transit = db.fetch_one("SELECT AVG(typical_transit_days) FROM routes WHERE origin_country = 'Indonesia'")[0]
        aus_transit = db.fetch_one("SELECT AVG(typical_transit_days) FROM routes WHERE origin_country = 'Australia'")[0]
        usa_transit = db.fetch_one("SELECT AVG(typical_transit_days) FROM routes WHERE origin_country = 'USA'")[0]
        self.assertLess(indo_transit, aus_transit)
        self.assertLess(aus_transit, usa_transit)

    def test_05_freight_rates_timeline_and_positivity(self):
        count = db.get_table_row_count("freight_rates")
        self.assertEqual(count, 51100, "Must have 35 routes x 4 vessels x 365 days = 51,100 freight rate observations")

        # Range and timeline
        stats = db.fetch_one("SELECT MIN(rate_usd_per_t), MIN(rate_date), MAX(rate_date), COUNT(DISTINCT rate_date) FROM freight_rates")
        min_rate, min_date_str, max_date_str, distinct_days = stats
        self.assertGreater(min_rate, 0, "All freight rates must be strictly positive")
        self.assertEqual(str(max_date_str), "2026-09-18", "Demo freight series must end on DEMO_AS_OF_DATE (2026-09-18)")
        self.assertEqual(str(min_date_str), "2025-09-19", "Demo freight series must start on 2025-09-19 for 365 days")
        self.assertEqual(distinct_days, 365, "Must have 365 contiguous daily observations")

    def test_06_market_data_timeline_and_ranges(self):
        count = db.get_table_row_count("market_data")
        self.assertEqual(count, 365, "Must have 365 daily market observations")

        stats = db.fetch_one("""
            SELECT MIN(bunker_price_vlsfo_usd_per_t), MAX(bunker_price_vlsfo_usd_per_t),
                   MIN(usd_inr_rate), MAX(usd_inr_rate),
                   MIN(bdi_index), MAX(bdi_index),
                   MIN(market_date), MAX(market_date)
            FROM market_data
        """)
        self.assertGreater(stats[0], 400.0, "VLSFO bunker price within realistic bounds")
        self.assertLess(stats[1], 1000.0, "VLSFO bunker price within realistic bounds")
        self.assertGreater(stats[2], 75.0, "USD/INR rate within realistic bounds")
        self.assertLess(stats[3], 95.0, "USD/INR rate within realistic bounds")
        self.assertGreater(stats[4], 500.0, "BDI within realistic bounds")
        self.assertEqual(str(stats[7]), "2026-09-18")
        self.assertEqual(str(stats[6]), "2025-09-19")

    def test_07_congestion_data_boundaries_and_port_coverage(self):
        count = db.get_table_row_count("congestion_data")
        self.assertEqual(count, 2555, "Must have 7 ports x 365 days = 2,555 congestion observations")

        stats = db.fetch_one("SELECT MIN(congestion_index), MAX(congestion_index), MIN(avg_waiting_hours) FROM congestion_data")
        self.assertGreaterEqual(stats[0], 0.0, "Congestion index >= 0")
        self.assertLessEqual(stats[1], 100.0, "Congestion index <= 100")
        self.assertGreaterEqual(stats[2], 0.0, "Waiting hours >= 0")

        # Port coverage
        ports_in_cong = db.fetch_all("SELECT DISTINCT port_id FROM congestion_data")
        self.assertEqual(len(ports_in_cong), 7)

    def test_08_determinism_and_reproducibility(self):
        # Generating with the same seed 42 must yield identical series
        f1 = generate_freight_rates_data(as_of_date=date(2026, 9, 18), history_days=365, seed=42)
        f2 = generate_freight_rates_data(as_of_date=date(2026, 9, 18), history_days=365, seed=42)
        self.assertEqual(f1, f2, "Freight generator must be strictly deterministic")

        m1 = generate_market_data(as_of_date=date(2026, 9, 18), history_days=365, seed=42)
        m2 = generate_market_data(as_of_date=date(2026, 9, 18), history_days=365, seed=42)
        self.assertEqual(m1, m2, "Market generator must be strictly deterministic")

        c1 = generate_congestion_data(as_of_date=date(2026, 9, 18), history_days=365, seed=42)
        c2 = generate_congestion_data(as_of_date=date(2026, 9, 18), history_days=365, seed=42)
        self.assertEqual(c1, c2, "Congestion generator must be strictly deterministic")

    def test_09_multi_voyage_schema_support(self):
        # Verify voyages table accepts scenario_id and voyage_sequence
        db.execute_query("""
            INSERT INTO voyages (
                voyage_id, scenario_id, voyage_sequence, cargo_reference,
                commodity_type, origin_country, destination_port_id,
                route_id, vessel_class, cargo_tonnage,
                planned_laycan_start, planned_laycan_end, required_delivery_date,
                status, data_origin
            ) VALUES (
                'TEST_VOYAGE_001', NULL, 1, 'CARGO-AU-01',
                'Coking Coal', 'Australia', 'INPRT',
                'RT_AUSTRALIA_PARADIP', 'Capesize', 150000.00,
                '2026-10-01', '2026-10-05', '2026-10-25',
                'PLANNED', 'ASSUMPTION'
            )
        """)
        v_check = db.fetch_one("SELECT voyage_id, voyage_sequence, cargo_tonnage FROM voyages WHERE voyage_id = 'TEST_VOYAGE_001'")
        self.assertIsNotNone(v_check)
        self.assertEqual(v_check[1], 1)
        self.assertEqual(v_check[2], 150000.00)
        db.execute_query("DELETE FROM voyages WHERE voyage_id = 'TEST_VOYAGE_001'")

    def test_10_full_validation_suite_passes(self):
        passed = run_validation()
        self.assertTrue(passed, "Validation suite must return True with 0 errors")


if __name__ == "__main__":
    unittest.main()
