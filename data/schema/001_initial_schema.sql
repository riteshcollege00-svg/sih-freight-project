-- =============================================================================
-- SIH 2026: Freight Forecasting & Intelligent Vessel Chartering for Bulk Cargo
-- Member 1: Data & Domain Foundation
-- File: 001_initial_schema.sql
-- Description: PostgreSQL 16+ DDL for all 11 Core Foundation & Consumer Tables
-- =============================================================================

-- Enable UUID extension if needed in future
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- 0. CLEANUP (Idempotent Migration Support)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS charter_scenarios CASCADE;
DROP TABLE IF EXISTS risk_events CASCADE;
DROP TABLE IF EXISTS optimization_results CASCADE;
DROP TABLE IF EXISTS voyages CASCADE;
DROP TABLE IF EXISTS forecasts CASCADE;
DROP TABLE IF EXISTS congestion_data CASCADE;
DROP TABLE IF EXISTS market_data CASCADE;
DROP TABLE IF EXISTS freight_rates CASCADE;
DROP TABLE IF EXISTS routes CASCADE;
DROP TABLE IF EXISTS vessels CASCADE;
DROP TABLE IF EXISTS ports CASCADE;

-- -----------------------------------------------------------------------------
-- 1. PORTS (Indian East Coast Destination Ports & Reference Data)
-- -----------------------------------------------------------------------------
CREATE TABLE ports (
    port_id VARCHAR(32) PRIMARY KEY,
    port_name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL DEFAULT 'India',
    coast VARCHAR(50) NOT NULL DEFAULT 'East Coast India',
    latitude NUMERIC(8, 4),
    longitude NUMERIC(8, 4),
    max_draft_m NUMERIC(5, 2) NOT NULL CHECK (max_draft_m > 0),
    max_loa_m NUMERIC(6, 2) NOT NULL CHECK (max_loa_m > 0),
    max_beam_m NUMERIC(5, 2) NOT NULL CHECK (max_beam_m > 0),
    handling_capacity_tpd NUMERIC(10, 2) NOT NULL CHECK (handling_capacity_tpd > 0),
    baseline_congestion_index NUMERIC(5, 2) NOT NULL CHECK (baseline_congestion_index >= 0 AND baseline_congestion_index <= 100),
    avg_turnaround_days NUMERIC(5, 2) NOT NULL CHECK (avg_turnaround_days > 0),
    demurrage_rate_usd_day NUMERIC(10, 2) NOT NULL CHECK (demurrage_rate_usd_day > 0),
    data_origin VARCHAR(20) NOT NULL CHECK (data_origin IN ('REAL', 'SYNTHETIC', 'ASSUMPTION', 'MODEL_OUTPUT', 'SIMULATION')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ports_country_coast ON ports(country, coast);

-- -----------------------------------------------------------------------------
-- 2. VESSELS (Bulk Carrier Classes & Technical Specifications)
-- -----------------------------------------------------------------------------
CREATE TABLE vessels (
    vessel_class VARCHAR(50) PRIMARY KEY,
    dwt NUMERIC(10, 2) NOT NULL CHECK (dwt > 0),
    cargo_capacity_mt NUMERIC(10, 2) NOT NULL CHECK (cargo_capacity_mt > 0),
    loa_m NUMERIC(6, 2) NOT NULL CHECK (loa_m > 0),
    beam_m NUMERIC(5, 2) NOT NULL CHECK (beam_m > 0),
    draft_m NUMERIC(5, 2) NOT NULL CHECK (draft_m > 0),
    service_speed_knots NUMERIC(4, 2) NOT NULL DEFAULT 12.50 CHECK (service_speed_knots > 0),
    fuel_consumption_tpd NUMERIC(5, 2) NOT NULL DEFAULT 28.00 CHECK (fuel_consumption_tpd > 0),
    data_origin VARCHAR(20) NOT NULL CHECK (data_origin IN ('REAL', 'SYNTHETIC', 'ASSUMPTION', 'MODEL_OUTPUT', 'SIMULATION')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 3. ROUTES (Origin Country to Indian Destination Port Combinations)
-- -----------------------------------------------------------------------------
CREATE TABLE routes (
    route_id VARCHAR(100) PRIMARY KEY,
    origin_country VARCHAR(100) NOT NULL,
    origin_port_region VARCHAR(100) NOT NULL,
    destination_port_id VARCHAR(32) NOT NULL REFERENCES ports(port_id) ON DELETE RESTRICT,
    distance_nm NUMERIC(10, 2) NOT NULL CHECK (distance_nm > 0),
    typical_transit_days NUMERIC(5, 2) NOT NULL CHECK (typical_transit_days > 0),
    bunker_consumption_factor NUMERIC(5, 2) NOT NULL DEFAULT 1.00 CHECK (bunker_consumption_factor > 0),
    data_origin VARCHAR(20) NOT NULL CHECK (data_origin IN ('REAL', 'SYNTHETIC', 'ASSUMPTION', 'MODEL_OUTPUT', 'SIMULATION')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_route_origin_dest UNIQUE (origin_country, destination_port_id)
);

CREATE INDEX idx_routes_origin_dest ON routes(origin_country, destination_port_id);

-- -----------------------------------------------------------------------------
-- 4. FREIGHT RATES (Daily Historical Freight Rates per Route & Vessel Class)
-- -----------------------------------------------------------------------------
CREATE TABLE freight_rates (
    id BIGSERIAL PRIMARY KEY,
    route_id VARCHAR(100) NOT NULL REFERENCES routes(route_id) ON DELETE CASCADE,
    vessel_class VARCHAR(50) NOT NULL REFERENCES vessels(vessel_class) ON DELETE RESTRICT,
    rate_date DATE NOT NULL,
    rate_usd_per_t NUMERIC(10, 2) NOT NULL CHECK (rate_usd_per_t > 0),
    data_origin VARCHAR(20) NOT NULL CHECK (data_origin IN ('REAL', 'SYNTHETIC', 'ASSUMPTION', 'MODEL_OUTPUT', 'SIMULATION')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_freight_route_vessel_date UNIQUE (route_id, vessel_class, rate_date)
);

CREATE INDEX idx_freight_rates_route_date ON freight_rates(route_id, rate_date);
CREATE INDEX idx_freight_rates_vessel_date ON freight_rates(vessel_class, rate_date);
CREATE INDEX idx_freight_rates_date ON freight_rates(rate_date);

-- -----------------------------------------------------------------------------
-- 5. MARKET DATA (Daily Global Bunker Fuel, FX, and Market Indicators)
-- -----------------------------------------------------------------------------
CREATE TABLE market_data (
    id BIGSERIAL PRIMARY KEY,
    market_date DATE NOT NULL UNIQUE,
    bunker_price_vlsfo_usd_per_t NUMERIC(10, 2) NOT NULL CHECK (bunker_price_vlsfo_usd_per_t > 0),
    bunker_price_ifo380_usd_per_t NUMERIC(10, 2) NOT NULL CHECK (bunker_price_ifo380_usd_per_t > 0),
    usd_inr_rate NUMERIC(8, 4) NOT NULL CHECK (usd_inr_rate > 0),
    bdi_index NUMERIC(10, 2) CHECK (bdi_index > 0),
    bci_index NUMERIC(10, 2) CHECK (bci_index > 0),
    bpi_index NUMERIC(10, 2) CHECK (bpi_index > 0),
    bsi_index NUMERIC(10, 2) CHECK (bsi_index > 0),
    bhsi_index NUMERIC(10, 2) CHECK (bhsi_index > 0),
    crude_oil_brent_usd NUMERIC(10, 2) CHECK (crude_oil_brent_usd > 0),
    data_origin VARCHAR(20) NOT NULL CHECK (data_origin IN ('REAL', 'SYNTHETIC', 'ASSUMPTION', 'MODEL_OUTPUT', 'SIMULATION')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_market_data_date ON market_data(market_date);

-- -----------------------------------------------------------------------------
-- 6. CONGESTION DATA (Daily Port-Specific Congestion & Waiting Times)
-- -----------------------------------------------------------------------------
CREATE TABLE congestion_data (
    id BIGSERIAL PRIMARY KEY,
    port_id VARCHAR(32) NOT NULL REFERENCES ports(port_id) ON DELETE CASCADE,
    congestion_date DATE NOT NULL,
    congestion_index NUMERIC(5, 2) NOT NULL CHECK (congestion_index >= 0 AND congestion_index <= 100),
    avg_waiting_hours NUMERIC(6, 2) NOT NULL CHECK (avg_waiting_hours >= 0),
    vessels_at_anchorage INTEGER CHECK (vessels_at_anchorage >= 0),
    vessels_at_berth INTEGER CHECK (vessels_at_berth >= 0),
    data_origin VARCHAR(20) NOT NULL CHECK (data_origin IN ('REAL', 'SYNTHETIC', 'ASSUMPTION', 'MODEL_OUTPUT', 'SIMULATION')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_congestion_port_date UNIQUE (port_id, congestion_date)
);

CREATE INDEX idx_congestion_port_date ON congestion_data(port_id, congestion_date);
CREATE INDEX idx_congestion_date ON congestion_data(congestion_date);

-- -----------------------------------------------------------------------------
-- 7. FORECASTS (Storage for Forecasting Models - Consumer: Member 2)
-- -----------------------------------------------------------------------------
CREATE TABLE forecasts (
    id BIGSERIAL PRIMARY KEY,
    route_id VARCHAR(100) NOT NULL REFERENCES routes(route_id) ON DELETE CASCADE,
    vessel_class VARCHAR(50) NOT NULL REFERENCES vessels(vessel_class) ON DELETE RESTRICT,
    forecast_generated_date DATE NOT NULL,
    target_date DATE NOT NULL,
    horizon_days INTEGER NOT NULL CHECK (horizon_days > 0),
    predicted_rate_usd_per_t NUMERIC(10, 2) NOT NULL CHECK (predicted_rate_usd_per_t > 0),
    confidence_lower_95 NUMERIC(10, 2) CHECK (confidence_lower_95 > 0),
    confidence_upper_95 NUMERIC(10, 2) CHECK (confidence_upper_95 > 0),
    model_version VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    data_origin VARCHAR(20) NOT NULL CHECK (data_origin IN ('REAL', 'SYNTHETIC', 'ASSUMPTION', 'MODEL_OUTPUT', 'SIMULATION')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_forecast_entry UNIQUE (route_id, vessel_class, forecast_generated_date, target_date, model_version)
);

CREATE INDEX idx_forecasts_route_target ON forecasts(route_id, target_date);
CREATE INDEX idx_forecasts_gen_date ON forecasts(forecast_generated_date);

-- -----------------------------------------------------------------------------
-- 8. VOYAGES (Cargo Chartering Requirements & Schedules - Consumer: Member 3 & 4)
-- -----------------------------------------------------------------------------
CREATE TABLE voyages (
    voyage_id VARCHAR(100) PRIMARY KEY,
    scenario_id VARCHAR(100) REFERENCES charter_scenarios(scenario_id) ON DELETE SET NULL,
    voyage_sequence INTEGER NOT NULL DEFAULT 1 CHECK (voyage_sequence > 0),
    cargo_reference VARCHAR(100) NOT NULL,
    commodity_type VARCHAR(50) NOT NULL DEFAULT 'Coking Coal',
    origin_country VARCHAR(100) NOT NULL,
    destination_port_id VARCHAR(32) NOT NULL REFERENCES ports(port_id) ON DELETE RESTRICT,
    route_id VARCHAR(100) REFERENCES routes(route_id) ON DELETE SET NULL,
    vessel_class VARCHAR(50) NOT NULL REFERENCES vessels(vessel_class) ON DELETE RESTRICT,
    cargo_tonnage NUMERIC(12, 2) NOT NULL CHECK (cargo_tonnage > 0),
    planned_laycan_start DATE NOT NULL,
    planned_laycan_end DATE NOT NULL,
    required_delivery_date DATE NOT NULL,
    actual_departure_date DATE,
    actual_arrival_date DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'PLANNED' CHECK (status IN ('DRAFT', 'PLANNED', 'CHARTERING', 'FIXED', 'IN_TRANSIT', 'DISCHARGING', 'COMPLETED', 'CANCELLED')),
    agreed_freight_usd_per_t NUMERIC(10, 2) CHECK (agreed_freight_usd_per_t > 0),
    data_origin VARCHAR(20) NOT NULL CHECK (data_origin IN ('REAL', 'SYNTHETIC', 'ASSUMPTION', 'MODEL_OUTPUT', 'SIMULATION')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_laycan_order CHECK (planned_laycan_end >= planned_laycan_start)
);

CREATE INDEX idx_voyages_scenario ON voyages(scenario_id);
CREATE INDEX idx_voyages_status ON voyages(status);
CREATE INDEX idx_voyages_destination ON voyages(destination_port_id);
CREATE INDEX idx_voyages_laycan ON voyages(planned_laycan_start, planned_laycan_end);

-- -----------------------------------------------------------------------------
-- 9. OPTIMIZATION RESULTS (Vessel Allocation & Timing Results - Consumer: Member 3)
-- -----------------------------------------------------------------------------
CREATE TABLE optimization_results (
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(100) NOT NULL,
    voyage_id VARCHAR(100) REFERENCES voyages(voyage_id) ON DELETE CASCADE,
    route_id VARCHAR(100) NOT NULL REFERENCES routes(route_id) ON DELETE RESTRICT,
    recommended_vessel_class VARCHAR(50) NOT NULL REFERENCES vessels(vessel_class) ON DELETE RESTRICT,
    recommended_charter_timing VARCHAR(50) NOT NULL, -- e.g., 'SPOT', 'FORWARD_1W', 'FORWARD_2W'
    recommended_laycan_start DATE NOT NULL,
    recommended_laycan_end DATE NOT NULL,
    estimated_freight_usd_per_t NUMERIC(10, 2) NOT NULL CHECK (estimated_freight_usd_per_t > 0),
    estimated_total_cost_usd NUMERIC(15, 2) NOT NULL CHECK (estimated_total_cost_usd > 0),
    estimated_demurrage_risk_usd NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (estimated_demurrage_risk_usd >= 0),
    objective_score NUMERIC(10, 4),
    solver_status VARCHAR(50) NOT NULL DEFAULT 'OPTIMAL',
    data_origin VARCHAR(20) NOT NULL CHECK (data_origin IN ('REAL', 'SYNTHETIC', 'ASSUMPTION', 'MODEL_OUTPUT', 'SIMULATION')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_opt_run_id ON optimization_results(run_id);
CREATE INDEX idx_opt_voyage_id ON optimization_results(voyage_id);

-- -----------------------------------------------------------------------------
-- 10. RISK EVENTS (Port, Route & Geopolitical Disruptions - Consumer: Member 4)
-- -----------------------------------------------------------------------------
CREATE TABLE risk_events (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    target_type VARCHAR(50) NOT NULL CHECK (target_type IN ('PORT', 'ROUTE', 'REGION', 'GLOBAL')),
    target_identifier VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    start_date DATE NOT NULL,
    expected_end_date DATE NOT NULL,
    estimated_delay_days NUMERIC(5, 2) NOT NULL DEFAULT 0 CHECK (estimated_delay_days >= 0),
    cost_impact_multiplier NUMERIC(5, 2) NOT NULL DEFAULT 1.00 CHECK (cost_impact_multiplier >= 1.00),
    description TEXT,
    data_origin VARCHAR(20) NOT NULL CHECK (data_origin IN ('REAL', 'SYNTHETIC', 'ASSUMPTION', 'MODEL_OUTPUT', 'SIMULATION')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_risk_dates CHECK (expected_end_date >= start_date)
);

CREATE INDEX idx_risk_events_target ON risk_events(target_type, target_identifier);
CREATE INDEX idx_risk_events_dates ON risk_events(start_date, expected_end_date);

-- -----------------------------------------------------------------------------
-- 11. CHARTER SCENARIOS (What-If Simulation Parameters & Payoffs - Consumer: Member 4)
-- -----------------------------------------------------------------------------
CREATE TABLE charter_scenarios (
    id BIGSERIAL PRIMARY KEY,
    scenario_id VARCHAR(100) UNIQUE NOT NULL,
    scenario_name VARCHAR(200) NOT NULL,
    description TEXT,
    bunker_price_shock_pct NUMERIC(6, 2) NOT NULL DEFAULT 0,
    freight_market_shock_pct NUMERIC(6, 2) NOT NULL DEFAULT 0,
    congestion_multiplier NUMERIC(5, 2) NOT NULL DEFAULT 1.00 CHECK (congestion_multiplier >= 0),
    usd_inr_exchange_rate NUMERIC(8, 4) CHECK (usd_inr_exchange_rate > 0),
    simulated_total_cost_usd NUMERIC(15, 2) CHECK (simulated_total_cost_usd > 0),
    risk_index NUMERIC(5, 2) CHECK (risk_index >= 0 AND risk_index <= 100),
    data_origin VARCHAR(20) NOT NULL CHECK (data_origin IN ('REAL', 'SYNTHETIC', 'ASSUMPTION', 'MODEL_OUTPUT', 'SIMULATION')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scenarios_id ON charter_scenarios(scenario_id);

-- =============================================================================
-- END OF SCHEMA DDL
-- =============================================================================
