
CREATE TABLE ref_data (
    my_sequence INT,
    my_costant VARCHAR(50),
    my_uuid CHAR(36),
    my_choice VARCHAR(50),
    my_integer INT,
    my_float FLOAT,
    my_decimal NUMERIC(15, 4),
    my_timestamp TIMESTAMP,
    my_date DATE,
    my_time TIMESTAMP,
    my_bit BLOB,
    my_bytes BLOB,
    my_string VARCHAR(50),
    my_bool NUMBER(1),
    my_json VARCHAR(300),
    CONSTRAINT pk PRIMARY KEY (my_sequence)
);

CREATE TABLE transactions (
    lane VARCHAR(10),
    id CHAR(36),
    event INT,
    ts TIMESTAMP,
    PRIMARY KEY (lane, id, event)
);
