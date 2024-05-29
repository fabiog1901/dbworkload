CREATE KEYSPACE bank WITH replication = {'class':'SimpleStrategy','replication_factor':1};

USE bank;

CREATE TABLE ref_data (
    my_sequence INT,
    my_costant VARCHAR,
    my_uuid UUID,
    my_choice VARCHAR,
    my_integer INT,
    my_float FLOAT,
    my_decimal DECIMAL,
    my_timestamp TIMESTAMP,
    my_date DATE,
    my_time TIME,
    my_bit BLOB,
    my_bytes BLOB,
    my_string VARCHAR,
    my_bool BOOLEAN,
    my_json TEXT,
    PRIMARY KEY (my_sequence)
);

CREATE TABLE transactions (
    lane VARCHAR,
    id UUID,
    event INT,
    ts TIMESTAMP,
    PRIMARY KEY ((lane, id, event))
);
