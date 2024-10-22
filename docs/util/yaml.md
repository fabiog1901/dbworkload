# yaml

## Generate YAML data generation file from a DDL SQL file

`dbworkload` can assist with generating a stub of the _data generation definition_ file, required by the [`csv`](./csv.md) command.

### Create the stub file

`yaml` accepts a file with DDL statements as input and will create a `.yaml` file as output.

```bash
dbworkload util yaml -i bank.ddl.sql
```

### Options

|Option | Usage  |
| ------ | ------ |
| `--input`<br><br>`-i` | A SQL file containing one or more `CREATE TABLE` statements ending in a semi colon. <br><br>Required: Yes <br> Default: None |

### Example

1. Create a DDL file. Let's call it `bank.ddl`.

    ```sql
    -- file: bank.ddl

    CREATE TABLE ref_data (
        acc_no BIGINT PRIMARY KEY,
        external_ref_id UUID,
        created_time TIMESTAMPTZ,
        acc_details VARCHAR
    );

    CREATE TABLE orders (
        acc_no BIGINT NOT NULL,
        id UUID NOT NULL default gen_random_uuid(),
        status VARCHAR NOT NULL,
        amount DECIMAL(15, 2),
        ts TIMESTAMPTZ default now(),
        CONSTRAINT pk PRIMARY KEY (acc_no, id)
    );
    ```

2. Run the `yaml` command, passing in `bank.ddl` as the input.

    ```bash
    dbworkload util yaml -i bank.ddl
    ```

3. Open `bank.yaml` output and inspect YAML tree.
    This is a configuration file with instructions on what type of data to generate.
    Check section [Types](#types) for a full list of available object types and arguments.

    ```yaml
    ref_data:
      - count: 100
        sort-by: []
        columns:
          acc_no:
            type: integer
            args:
              min: -9223372036854775807
              max: 9223372036854775807
              seed: 64
              null_pct: 0.3
              array: 0
          external_ref_id:
            type: uuid
            args:
              seed: 76
              null_pct: 0.25
              array: 0
          created_time:
            type: timestamp
            args:
              start: "2000-01-01"
              end: "2024-12-31"
              format: "%Y-%m-%d %H:%M:%S.%f"
              seed: 78
              null_pct: 0.37
              array: 0
          acc_details:
            type: string
            args:
              min: 10
              max: 30
              prefix: ""
              seed: 54
              null_pct: 0.38
              array: 0
    orders:
      - count: 100
        sort-by: []
        columns:
          acc_no:
            type: integer
            args:
              min: -9223372036854775807
              max: 9223372036854775807
              seed: 83
              null_pct: 0.0
              array: 0
        id:
          type: uuid
          args:
            seed: 49
            null_pct: 0.0
            array: 0
        status:
          type: string
          args:
            min: 10
            max: 30
            prefix: ""
            seed: 58
            null_pct: 0.0
            array: 0
        amount:
          type: float
          args:
            min: 0
            max: 10000000000000
            round: 2
            seed: 11
            null_pct: 0.33
            array: 0
        ts:
          type: timestamp
          args:
            start: "2000-01-01"
            end: "2024-12-31"
            format: "%Y-%m-%d %H:%M:%S.%f"
            seed: 100
            null_pct: 0.26
            array: 0
    ```

## Types

Below is a table with all available generators and their arguments

| Generator | Arguments              | Default        |
|-----------|------------------------|----------------|
| constant  | value `str`            |"simplefaker"   |
| sequence  | start `int`            | 0              |
| integer   | min `int`              | 1              |
|           | max `int`              | 1,000,000,000  |
| float     | min `int`              | 1              |
|           | max `int`              | 1,000,000      |
|           | round `int`            | 2              |
| string    | min `int`              | 10             |
|           | max `int`              | 50             |
|           | prefix `str`           | <blank\>       |
| json      | min `int`              | 10             |
|           | max `int`              | 50             |
| choice    | population `list[str]` | ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] |
|           | weights  `list[int]`   | empty list     |
|           | cum_weights `list[int]`| empty list     |
| timestamp | start `str`            | "2000-01-01"   |
|           | end `str`              | "2024-12-31"   |
|           | format `str`           | "%Y-%m-%d %H:%M:%S.%f"|
| date      | start `str`            | "2000-01-01"   |
|           | end `str`              | "2024-12-31"   |
|           | format `str`           | "%Y-%m-%d"     |
| time      | start `str`            | "07:30:00"     |
|           | end `str`              | "22:30:00"     |
|           | micros `bool`          | false          |
| uuid      |                        |                |
| bool      |                        |                |
| bit       | size `int`             | 10             |
| bytes     | size `int`             | 10             |

Furthermore, all but `constant`, `sequence`, `json` take these common arguments

| Arguments              | Default        |
| -----------------------| ---------------|
| seed `float`           | 0              |
| null_pct `float`       | 0              |
| array `int`            | 0              |

## See also

- [Seed the database tables](/docs/getting_started/2.md)
