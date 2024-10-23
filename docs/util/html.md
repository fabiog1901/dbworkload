# html

## Save charts to HTML from the dbworkload statistics CSV file

`dbworkload` can create an interactive chart in a self contained HTML file.

### Create the HTML file

`html` accepts a `.csv` file as input and will create a `.html` as output.

```bash
dbworkload util html -i Bank.20241022_175006.csv
```

### Options

|Option | Usage  |
| ------ | ------ |
| `--input`<br><br>`-i` | A `.csv` file resulting from running a workload with the `-s` option. <br><br>Required: Yes <br> Default: None |

### Example

1. Run the `html` command, passing in your CSV as the input.

    ```bash
    dbworkload util html -i Bank.20241021_145825.csv 
    ```

2. Open resulting file `Bank.20241021_145825.html` in your browser

    ![html](../getting_started/media//html.png)

## See also

- [Plot the metrics](../getting_started/7.md)
