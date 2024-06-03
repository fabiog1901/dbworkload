CREATE DATABASE bank;

USE bank;

CREATE TABLE IF NOT EXISTS ref_data (
    my_sequence INT,
    my_costant VARCHAR(50),
    my_uuid UUID,
    my_choice VARCHAR(50),
    my_integer INT,
    my_float FLOAT,
    my_decimal DECIMAL(15, 4),
    my_timestamp TIMESTAMP,
    my_date DATE,
    my_time TIME,
    my_bit BIT(10),
    my_bytes BINARY,
    my_string VARCHAR(50),
    my_bool BOOL,
    my_json JSON,
    CONSTRAINT pk PRIMARY KEY (my_sequence)
);

CREATE TABLE IF NOT EXISTS transactions (
    lane VARCHAR(10),
    id UUID,
    event INT,
    ts TIMESTAMP,
    PRIMARY KEY (lane, id, event)
);
