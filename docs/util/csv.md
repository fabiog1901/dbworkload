# csv

- You can seed a database quickly by letting `dbworkload` generate pseudo-random data and import it.
- `dbworkload` takes the DDL as an input and creates an intermediate YAML file, with the definition of what data you want to create (a string, a number, a date, a bool..) based on the column data type.
- You then refine the YAML file to suit your needs, for example, the size of the string, a range for a date, the precision for a decimal, a choice among a discrete list of values..
- You can also specify what is the percentage of NULL for any column, or how many elements in an ARRAY type.
- You then specify the total row count, how many rows per file, and in what order, if any, to sort by.
- Then `dbworkload` will generate the data into CSV or TSV files, compress them if so requested.
- You can then optionally merge-sort the files using command `merge`.

Write up blog: [Generate multiple large sorted csv files with pseudo-random data](https://dev.to/cockroachlabs/generate-multiple-large-sorted-csv-files-with-pseudo-random-data-1jo4)

Consult file `workloads/postgres/bank.yaml` for a list of all available generators and options.
