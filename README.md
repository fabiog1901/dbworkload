# dbworkload - DBMS workload utility

## Overview

The goal of `dbworkload` is to ease the creation and execution of bespoke database workload scripts.

The user is responsible for coding the workload logic as a Python `class`,
while `dbworkload` takes care of providing ancillary features, such as configuring the
workload concurrency, duration and/or iteration, and more.

The user, by coding the class, has complete control of the workload flow:
what transactions are executed in which order, and what statements are included in each transaction,
plus what data to insert and how to generate it and manipulate it.

### Database seeding

`dbworkload` can help with seeding a database by creating CSV files with random generated data,
whose definition is supplied in a YAML file and can be extracted from a DDL SQL file.

### Software requirements

`dbworkload` requires at least Python 3.8 and the `pip` utility, installed and upgraded.

`dbworkload` dependencies are installed automatically by the `pip` tool.

It has run successfully on Ubuntu 20.04+, MacOSX on both Intel and Apple silicone.

## Supported DBMS drivers

### 1. psycopg (PostgreSQL, CockroachDB)

Driver documentation: [Psycopg 3](https://www.psycopg.org/psycopg3/docs/).

```bash
# installation
pip install dbworkload[postgres]

# sample use
dbworkload run -w workloads/postgres/bank.py \
  --uri 'postgres://cockroach:cockroach@localhost:26257/bank?sslmode=require' \
  -l debug --args '{"read_pct":50}' -i 1 -c 1
```

### 2. mysql-connector-python (MySQL, TiDB, Singlestore)

Driver documentation: [MySQL Connector/Python Developer Guide](https://dev.mysql.com/doc/connector-python/en/).

```bash
# installation
pip3 install dbworkload[mysql]

# sample use
dbworkload run -w workloads/mysql/bank.py \
  --uri 'user=root,password=London123,host=localhost,port=3306,database=bank,client_flags=SSL' \
   --driver mysql --args '{"read_pct":50}' -i 10
```

### 3. mariadb (MariaDB)

Driver documentation: [MariaDB Connector/Python](https://mariadb.com/docs/server/connect/programming-languages/python/).

```bash
# installation
pip3 install dbworkload[mariadb]

# sample use
dbworkload run -w workloads/mariadb/bank.py \
  --uri 'user=user1,password=password1,host=localhost,port=3306,database=bank' \
  --driver maria --args '{"read_pct":50}' -i 10
```

### 4. oracledb (Oracle)

Driver documentation: [python-oracledb’s documentation](https://python-oracledb.readthedocs.io/en/latest/index.html).

```bash
# installation
pip3 install dbworkload[oracle]

# sample use
dbworkload run -w workloads/oracle/bank.py \
  --uri "user=admin,password=password1,dsn="myhost.host2.us-east-1.rds.amazonaws.com:1521/OMS" \
  --driver oracle --args='{"read_pct":50}' -i 10
```

### 5. pyodbc (MS SQLServer)

Under construction...

Driver documentation: [Python SQL driver](https://learn.microsoft.com/en-us/sql/connect/python/python-driver-for-sql-server?view=sql-server-ver16).

```bash
# installation
pip3 install dbworkload[sqlserver]

# sample use
dbworkload run -w workloads/sqlserver/bank.py \
  --uri "" \
   --driver sqlserver --args='{"read_pct":50}' -i 10
```

### 6. pymongo (MongoDB)

Driver documentation: [MongoDB PyMongo Documentation](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/).

```bash
# installation
pip3 install dbworkload[mongo]

# sample use
dbworkload run -w workloads/mongo/bank.py \
  --uri "mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000" \
  --args='{"read_pct":50}' -i 10
```

### 7. scylla-driver (Cassandra, ScyllaDB)

Under construction...

Driver documentation: [Python Driver for Scylla and Apache Cassandra](https://python-driver.docs.scylladb.com/stable/).

```bash
# installation
pip3 install dbworkload[cassandra]

# sample use
dbworkload run -w workloads/cassandra/bank.py \
  --uri "" \
   --driver cassandra --args='{"read_pct":50}' -i 10
```

## Example (using PostgreSQL Server and CockroachDB)

Class `Bank` in file `workloads/postgres/bank.py` is an example of one such user-created workload.
The class defines 3 simple transactions that have to be executed by `dbworkload`.
Have a look at the `bank.py`, `bank.yaml` and `bank.sql` in the `workload/postgres/` folder in this project.

Head to file `workload/postgres/bank.sql` to see what the database schema look like. We have 2 tables:

- the `transactions` table, where we record the bank payment transactions.
- the `ref_data` table.

Take a close look at this last table: each column represent a different type, which brings us to the next file.

File `bank.yaml` is the data generation definition file.
For each column of table `ref_data`, we deterministically generate random data.
This file is meant as a guide to show what type of data can be generated, and what args are required.

File `bank.py` defines the workload.
The workload is defined as a class object.
The class defines 2 methods: `loop()` and the constructor, `__init__()`.
All other methods are part of the application logic of the workload.
Read the comments along the code for more information.

Let's run the sample **Bank** workload.

### Step 0 - env setup

```bash
# using ubuntu 20.04 LTS
sudo apt update
sudo apt install -y python3-pip

# upgrade pip - must have pip version 20.3+ 
pip3 install --upgrade pip

pip3 install dbworkload[postgres]

mkdir workloads
cd workloads

# the workload class
wget https://raw.githubusercontent.com/fabiog1901/dbworkload/main/workloads/postgres/bank.py

# the DDL file
wget https://raw.githubusercontent.com/fabiog1901/dbworkload/main/workloads/postgres/bank.sql

# the data generation definition file
wget https://raw.githubusercontent.com/fabiog1901/dbworkload/main/workloads/postgres/bank.yaml
```

### Step 1 - init the workload

Make sure your **CockroachDB** cluster or **PostgreSQL** server is up and running.
Please note: this guide assumes the database server and dbworkload are both runnining locally and can communicate with each other via `localhost`.

Connect to the SQL prompt and execute the DDL statements in the `bank.sql` file.
In CockroachDB, you can simply run

```sql
sql> \i bank.sql
```

Next, generate some CSV data to seed the database:

```bash
dbworkload util csv -i bank.yaml -x 1
```

The CSV files will be located inside a `bank` directory.

```bash
$ ls -lh bank
total 1032
-rw-r--r--  1 fabio  staff   513K Apr  9 13:01 ref_data.0_0_0.csv

$ head -n2 bank/ref_data.0_0_0.csv 
0       simplefaker     b66ab5dc-1fcc-4ac8-8ad0-70bbbb463f00    alpha   16381   {124216.6,416559.9,355271.42,443666.45,689859.03,461510.94,31766.46,727918.45,361202.5,561364.1}        12421672576.9632        2022-10-18 04:57:37.613512      2022-10-18     13:36:48 1001010011      \xe38a2e10b400a8e77eda  {ID-cUJeNcMZ,ID-mWxhyiqN,ID-0FnlVOO5}   0       "{""k"":""cUJNcMZ""}"
1       simplefaker     f2ebb78a-5af3-4755-8c22-2ad06aa3b26c    bravo   39080           35527177861.6551        2022-12-25 09:12:04.771673      2022-12-25      13:05:42        0110111101      \x5a2efedf253aa3fbeea8  {ID-gQkRkMxIkSjihWcWTcr,ID-o7iDzl9AMJoFfduo6Hz,ID-5BS3MlZgOjxFZRBgBmf}  0       "{""k"":""5Di0UHLWMEuR7""}"
```

Now you can import the CSV file.
In CockroachDB, my favorite method is to use a webserver to serve the CSV file.
Open a new terminal then start a simple python server

```bash
cd workloads
cd bank
python3 -m http.server 3000
```

If you open your browser at <http://localhost:3000> you should see file `ref_data.0_0_0.csv` being served.

At the SQL prompt, import the file

```sql
sql> IMPORT INTO ref_data CSV DATA ('http://localhost:3000/ref_data.0_0_0.csv') WITH delimiter = e'\t'; 
```

In PostgreSQL Server, at the SQL prompt, just use `COPY`

```sql
bank=# COPY ref_data FROM '/Users/fabio/workloads/bank/ref_data.0_0_0.csv' WITH CSV DELIMITER AS e'\t';
COPY 100
Time: 2.713 ms
```

### Step 2 - Run the workload

Run the workload using 4 connections for 120 seconds or 100k cycles, whichever comes first.

```bash
# CockroachDB
dbworkload run -w bank.py -c 4 --uri 'postgres://root@localhost:26257/bank?sslmode=disable' -d 120 -i 100000

# PostgreSQL
dbworkload run -w bank.py -c 4 --uri 'postgres://fabio:postgres@localhost:5432/bank?sslmode=disable' -d 120 -i 100000
```

`dbworkload` will output rolling statistics about throughput and latency for each transaction in your workload class

```text
  elapsed  id               threads    tot_ops    tot_ops/s    period_ops    period_ops/s    mean(ms)    p50(ms)    p90(ms)    p95(ms)    p99(ms)    max(ms)
---------  -------------  ---------  ---------  -----------  ------------  --------------  ----------  ---------  ---------  ---------  ---------  ---------
        8  __cycle__              4        190        23.00           190           19.00      107.20      53.90     200.14     200.71     202.06     204.84
        8  read                   4         97        12.00            97            9.00       25.59      18.81      51.72      52.71      68.33      81.11
        8  txn1_new               4         93        11.00            93            9.00       46.17      46.93      48.44      49.08      61.33      67.98
        8  txn2_verify            4         93        11.00            93            9.00       76.12      83.02      84.46      84.56      95.24     102.75
        8  txn3_finalize          4         93        11.00            93            9.00       69.99      69.03      80.65      83.21      93.16      99.95 
[...]
```

You can always use **pgAdmin** for PostgreSQL Server or the **DB Console** for CockroachDB to view your workload, too.

There are many built-in options.
Check them out with

```bash
dbworkload --help
```

## How it works

It’s helpful to understand first what `dbworkload` does:

- At runtime, `dbworkload` first imports the class you pass, `bank.py`.

- It spawns _n_ threads for concurrent execution (see next section on Concurrency).
- By default, it sets the connection to `autocommit` mode.
- Each thread creates a database connection - no need for a connection pool.
- In a loop, each `dbworkload` thread will:
  - execute function `loop()` which returns a list of functions.
  - execute each function in the list sequentially. Each function, typically, executes a SQL statement/transaction.
- Execution stats are funneled back to the _MainThread_, which aggregates and, optionally, prints them to _stdout_ and saves them to a CSV file.
- If the connection drops, it will recreate it. You can also program how long you want the connection to last.
- `dbworkload` stops once a limit has been reached (iteration/duration), or you Ctrl+C.

## Concurrency - processes and threads

`dbworkload` uses both the `multiprocessing` and `threading` library to achieve high concurrency, that is, opening multiple connections to the DBMS.

There are 2 parameters that can be used to configure how many processes you want to create, and for each process, how many threads:

- `--procs/-x`, to configure the count of processes (defaults to the CPU count)
- `--concurrency/-c`, to configure the total number of connections (also referred to as _executing threads_)

`dbworkload` will spread the load across the processes, so that each process has an even amount of threads.

Example: if we set `--procs 4` and `--concurrency 10`, dbworkload will create as follows:

- Process-1: MainThread + 1 extra thread. Total = 2
- Process-2: MainThread + 1 extra thread. Total = 2
- Process-3: MainThread + 2 extra threads. Total = 3
- Process-4: MainThread + 2 extra threads. Total = 3

Total executing threads/connections = 10

This allows you to fine tune the count of Python processes and threads to fit your system.

Furthermore, each _executing thread_ receives a unique ID (an integer).
The ID is passed to the workload class with function `setup()`, along with the total count of threads, i.e. the value passed to `-c/--concurrency`.
You can leverage the ID and the thread count in various ways, for example, to have each thread process a subset of a dataset.

## Generating CSV files

- You can seed a database quickly by letting `dbworkload` generate pseudo-random data and import it.
- `dbworkload` takes the DDL as an input and creates an intermediate YAML file, with the definition of what data you want to create (a string, a number, a date, a bool..) based on the column data type.
- You then refine the YAML file to suit your needs, for example, the size of the string, a range for a date, the precision for a decimal, a choice among a discrete list of values..
- You can also specify what is the percentage of NULL for any column, or how many elements in an ARRAY type.
- You then specify the total row count, how many rows per file, and in what order, if any, to sort by.
- Then `dbworkload` will generate the data into CSV or TSV files, compress them if so requested.
- You can then optionally merge-sort the files using command `merge`.

Write up blog: [Generate multiple large sorted csv files with pseudo-random data](https://dev.to/cockroachlabs/generate-multiple-large-sorted-csv-files-with-pseudo-random-data-1jo4)

Find out more on the `yaml`, `csv` and `merge` commands by running

```bash
dbworkload util --help
```

Consult file `workloads/postgres/bank.yaml` for a list of all available generators and options.

## Limitations

## Acknowledgments

Some methods and classes have been taken and modified from, or inspired by, <https://github.com/cockroachdb/movr>
