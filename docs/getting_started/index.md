# Getting Started

Example using PostgreSQL Server and CockroachDB.

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
