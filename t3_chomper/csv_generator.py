"""CLI for generating CSV import files for SiriusT3 instrument"""

import click
from io import StringIO

from t3_chomper.formatters import (
    generate_registration_pka_file,
    TrayFormat,
)


@click.command()
@click.option(
    "--regi",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Registration CSV file with sample information",
)
@click.option(
    "--pka",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="CSV file with formatted pKa estimates",
)
@click.option(
    "--output", required=True, type=click.Path(exists=False), help="Output directory"
)
@click.option(
    "--protocol", required=True, type=click.Choice(TrayFormat, case_sensitive=False)
)
def t3_gencsv(protocol, regi, pka, output):
    click.echo(f"Generating {protocol} CSV for import")
    merged_df = generate_registration_pka_file(registration_csv=regi, pka_csv=pka)
    buffer = StringIO(merged_df.to_csv(None, index=False))
    formatter = protocol.value(input_csv=buffer)
    click.echo(f"Found {formatter.num_samples} samples with estimated pKa values.")
    formatter.generate_csv_files(output_dir=output)
