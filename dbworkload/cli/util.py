#!/usr/bin/python

from pathlib import Path
from typing import Optional
import dbworkload.models.run
import dbworkload.models.util
import dbworkload.utils.common
from dbworkload.cli.dep import Param, EPILOG
import typer


app = typer.Typer(
    epilog=EPILOG,
    no_args_is_help=True,
    help="Various utils.",
)


@app.command(
    "csv",
    epilog=EPILOG,
    no_args_is_help=True,
    help="Generate CSV files from a YAML data generation file.",
)
def util_csv(
    input: Optional[Path] = typer.Option(
        ...,
        "--input",
        "-i",
        help="Filepath to the YAML data generation file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        show_default=False,
        help="Output directory for the CSV files. Defaults to <input-basename>.",
        exists=False,
        file_okay=False,
        dir_okay=True,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
    procs: int = Param.Procs,
    csv_max_rows: int = Param.CSVMaxRows,
    http_server_hostname: str = typer.Option(
        None,
        "-n",
        "--hostname",
        show_default=False,
        help="The hostname of the http server that serves the CSV files.",
    ),
    http_server_port: int = typer.Option(
        3000,
        "-p",
        "--port",
        help="The port of the http server that servers the CSV files.",
    ),
    table_name: str = typer.Option(
        "table_name",
        "--table-name",
        "-t",
        help="The table name used in the import statement.",
    ),
    compression: str = typer.Option(
        None, "-c", "--compression", help="The compression format."
    ),
    delimiter: str = typer.Option(
        "\t",
        "-d",
        "--delimiter",
        help='The delimeter char to use for the CSV files. Defaults to "tab".',
        show_default=False,
    ),
):
    dbworkload.models.util.util_csv(
        input=input,
        output=output,
        compression=compression,
        procs=procs,
        csv_max_rows=csv_max_rows,
        delimiter=delimiter,
        http_server_hostname=http_server_hostname,
        http_server_port=http_server_port,
        table_name=table_name,
    )


@app.command(
    "yaml",
    epilog=EPILOG,
    no_args_is_help=True,
    help="Generate YAML data generation file from a DDL SQL file.",
)
def util_yaml(
    input: Optional[Path] = typer.Option(
        ...,
        "--input",
        "-i",
        help="Filepath to the DDL SQL file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        show_default=False,
        help="Output filepath. Defaults to <input-basename>.yaml.",
        exists=False,
        file_okay=True,
        dir_okay=True,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
):
    dbworkload.models.util.util_yaml(input=input, output=output)


@app.command(
    "merge",
    epilog=EPILOG,
    no_args_is_help=True,
    help="Merge multiple sorted CSV files into 1+ files.",
)
def util_merge(
    input: Optional[Path] = typer.Option(
        ...,
        "--input",
        "-i",
        help="Directory of files to be merged",
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        show_default=False,
        help="Output filepath. Defaults to <input>.merged.",
        exists=False,
        file_okay=True,
        dir_okay=True,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
    csv_max_rows: int = Param.CSVMaxRows,
):
    dbworkload.models.util.util_merge(input, output, csv_max_rows)
