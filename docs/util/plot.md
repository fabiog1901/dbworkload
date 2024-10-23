# plot

## Plot terminal charts from the statistics CSV file

`dbworkload` can plot terminal charts so you can inspect the workload directly from the instance
you are running the workload.

### Plot the metrics in the workload statistic CSV file

`plot` accepts a `.csv` file as input and will output directly to `stdout`.

```bash
dbworkload util plot -i Bank.20241022_175006.csv
```

### Options

|Option | Usage  |
| ------ | ------ |
| `--input`<br><br>`-i` | A `.csv` file resulting from running a workload with the `-s` option. <br><br>Required: Yes <br> Default: None |

### Example

Run the `plot` command, passing in your CSV as the input.

```bash
dbworkload util plot -i Bank.20241021_145825.csv 
```

The output is displayed right on the terminal

![plot](../getting_started/media//plot.png)

## See also

- [Plot the metrics](../getting_started/7.md)
