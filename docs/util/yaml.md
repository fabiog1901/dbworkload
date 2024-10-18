# yaml

## Generate YAML data generation file from a DDL SQL file

CREATE TABLE ref_data (
    my_sequence BIGINT PRIMARY KEY,
    my_constant VARCHAR,
    my_uuid UUID,
    my_choice VARCHAR,
    my_integer BIGINT,
    my_float FLOAT ARRAY,
    my_decimal DECIMAL(15, 4),
    my_timestamp TIMESTAMPTZ,
    my_date DATE,
    my_time TIME,
    my_bit BIT(10),
    my_bytes BYTEA,
    my_string VARCHAR[],
    my_bool BOOL,
    my_json JSONB
);
