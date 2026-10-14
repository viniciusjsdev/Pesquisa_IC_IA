CREATE SCHEMA dw;

CREATE TABLE dw.schema_migrations (
    version integer PRIMARY KEY,
    source_fingerprint char(64) NOT NULL,
    loaded_at_utc timestamptz NOT NULL DEFAULT now(),
    source_checks jsonb NOT NULL
);

CREATE TABLE dw.source_file (
    source_file_id integer PRIMARY KEY,
    domain text NOT NULL CHECK (domain IN ('industrial', 'financeiro')),
    period_index smallint NOT NULL CHECK (period_index BETWEEN 0 AND 2),
    table_name text NOT NULL,
    pk_column text NOT NULL,
    raw_schema text NOT NULL,
    source_path text NOT NULL,
    sha256 char(64) NOT NULL,
    row_count integer NOT NULL CHECK (row_count > 0),
    UNIQUE (domain, period_index, table_name)
);

CREATE TABLE dw.dim_source_period (
    period_index smallint PRIMARY KEY,
    industrial_folder text NOT NULL,
    financeiro_folder text NOT NULL
);

CREATE TABLE dw.dim_day (
    day date PRIMARY KEY,
    year integer NOT NULL,
    month integer NOT NULL,
    day_of_month integer NOT NULL
);

CREATE TABLE dw.dim_product (
    product_id integer PRIMARY KEY,
    period_index smallint NOT NULL REFERENCES dw.dim_source_period,
    source_file_id integer NOT NULL REFERENCES dw.source_file,
    original_id integer NOT NULL,
    name text NOT NULL,
    unit text,
    UNIQUE (period_index, original_id)
);

CREATE TABLE dw.dim_machine (
    machine_id integer PRIMARY KEY,
    period_index smallint NOT NULL REFERENCES dw.dim_source_period,
    source_file_id integer NOT NULL REFERENCES dw.source_file,
    original_id integer NOT NULL,
    name text NOT NULL,
    production_line text,
    UNIQUE (period_index, original_id)
);

CREATE TABLE dw.dim_material (
    material_id integer PRIMARY KEY,
    period_index smallint NOT NULL REFERENCES dw.dim_source_period,
    source_file_id integer NOT NULL REFERENCES dw.source_file,
    original_id integer NOT NULL,
    name text NOT NULL,
    unit text,
    UNIQUE (period_index, original_id)
);

CREATE TABLE dw.dim_material_lot (
    material_lot_id integer PRIMARY KEY,
    period_index smallint NOT NULL REFERENCES dw.dim_source_period,
    source_file_id integer NOT NULL REFERENCES dw.source_file,
    original_id integer NOT NULL,
    material_id integer NOT NULL REFERENCES dw.dim_material,
    received_on date,
    UNIQUE (period_index, original_id)
);

CREATE TABLE dw.fact_operation (
    operation_id integer PRIMARY KEY,
    source_file_id integer NOT NULL REFERENCES dw.source_file,
    period_index smallint NOT NULL REFERENCES dw.dim_source_period,
    original_id integer NOT NULL,
    operation_day date REFERENCES dw.dim_day,
    order_id integer NOT NULL,
    machine_id integer NOT NULL REFERENCES dw.dim_machine,
    product_id integer NOT NULL REFERENCES dw.dim_product,
    started_at timestamp,
    ended_at timestamp,
    quantity_reported integer,
    energy_kwh numeric,
    setup_minutes numeric,
    order_dates_inverted boolean NOT NULL,
    interval_invalid boolean NOT NULL,
    outside_source_label boolean NOT NULL,
    UNIQUE (source_file_id, original_id)
);

CREATE TABLE dw.fact_downtime (
    downtime_id integer PRIMARY KEY,
    source_file_id integer NOT NULL REFERENCES dw.source_file,
    period_index smallint NOT NULL REFERENCES dw.dim_source_period,
    original_id integer NOT NULL,
    start_day date REFERENCES dw.dim_day,
    machine_id integer NOT NULL REFERENCES dw.dim_machine,
    started_at timestamp,
    ended_at timestamp,
    duration_minutes numeric,
    interval_invalid boolean NOT NULL,
    outside_source_label boolean NOT NULL,
    UNIQUE (source_file_id, original_id)
);

CREATE TABLE dw.fact_sale (
    sale_id integer PRIMARY KEY,
    source_file_id integer NOT NULL REFERENCES dw.source_file,
    period_index smallint NOT NULL REFERENCES dw.dim_source_period,
    original_id integer NOT NULL,
    sale_day date REFERENCES dw.dim_day,
    product_id integer NOT NULL REFERENCES dw.dim_product,
    quantity_sold integer,
    unit_price numeric,
    observed_sales_value numeric,
    outside_source_label boolean NOT NULL,
    UNIQUE (source_file_id, original_id)
);

CREATE TABLE dw.fact_financial_observation (
    observation_id integer PRIMARY KEY,
    source_file_id integer NOT NULL REFERENCES dw.source_file,
    period_index smallint NOT NULL REFERENCES dw.dim_source_period,
    original_id integer NOT NULL,
    observed_day date REFERENCES dw.dim_day,
    reported_revenue double precision,
    reported_net_profit double precision,
    source_float boolean NOT NULL DEFAULT true,
    outside_source_label boolean NOT NULL,
    UNIQUE (source_file_id, original_id)
);

CREATE TABLE dw.fact_quality_inspection (
    inspection_id integer PRIMARY KEY,
    source_file_id integer NOT NULL REFERENCES dw.source_file,
    period_index smallint NOT NULL REFERENCES dw.dim_source_period,
    original_id integer NOT NULL,
    inspection_day date REFERENCES dw.dim_day,
    production_lot_id integer NOT NULL,
    order_id integer NOT NULL,
    product_id integer NOT NULL REFERENCES dw.dim_product,
    approved_units integer,
    rejected_units integer,
    lot_quantity integer,
    inspected_exceeds_lot boolean NOT NULL,
    outside_source_label boolean NOT NULL,
    UNIQUE (source_file_id, original_id)
);

CREATE TABLE dw.fact_material_consumption (
    consumption_id integer PRIMARY KEY,
    source_file_id integer NOT NULL REFERENCES dw.source_file,
    period_index smallint NOT NULL REFERENCES dw.dim_source_period,
    original_id integer NOT NULL,
    registered_day date REFERENCES dw.dim_day,
    operation_id integer NOT NULL REFERENCES dw.fact_operation,
    material_id integer NOT NULL REFERENCES dw.dim_material,
    material_lot_id integer NOT NULL REFERENCES dw.dim_material_lot,
    quantity_consumed numeric,
    outside_source_label boolean NOT NULL,
    UNIQUE (source_file_id, original_id)
);

CREATE TABLE dw.fact_material_price_observation (
    price_observation_id integer PRIMARY KEY,
    source_file_id integer NOT NULL REFERENCES dw.source_file,
    period_index smallint NOT NULL REFERENCES dw.dim_source_period,
    original_id integer NOT NULL,
    purchase_day date REFERENCES dw.dim_day,
    material_id integer NOT NULL REFERENCES dw.dim_material,
    material_lot_id integer NOT NULL REFERENCES dw.dim_material_lot,
    unit_price numeric,
    outside_source_label boolean NOT NULL,
    UNIQUE (source_file_id, original_id)
);

CREATE INDEX fact_operation_day_machine_idx ON dw.fact_operation (operation_day, machine_id);
CREATE INDEX fact_operation_day_product_idx ON dw.fact_operation (operation_day, product_id);
CREATE INDEX fact_downtime_day_machine_idx ON dw.fact_downtime (start_day, machine_id);
CREATE INDEX fact_sale_day_product_idx ON dw.fact_sale (sale_day, product_id);
CREATE INDEX fact_financial_observation_day_idx ON dw.fact_financial_observation (observed_day);
CREATE INDEX fact_quality_inspection_day_product_idx ON dw.fact_quality_inspection (inspection_day, product_id);
CREATE INDEX fact_material_consumption_day_material_idx ON dw.fact_material_consumption (registered_day, material_id);
CREATE INDEX fact_material_price_day_material_idx ON dw.fact_material_price_observation (purchase_day, material_id);
