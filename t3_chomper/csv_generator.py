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
    "--filter-file",
    required=False,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="File to limit entries from the regi file. Only samples included in the filter file will be considered.",
)
@click.option(
    "--sample-col",
    required=False,
    default="sample",
    type=str,
    help="Name of sample/ID column. Used for joining across files.",
)
@click.option(
    "--output", required=True, type=click.Path(exists=False), help="Output directory"
)
@click.option(
    "--protocol", required=True, type=click.Choice(TrayFormat, case_sensitive=False)
)
@click.option(
    "--concentration",
    required=False,
    default=10.0,
    type=float,
    help="Sample concentration in mM (default: 10.0)",
)
@click.option(
    "--volume",
    required=False,
    default=5.0,
    type=float,
    help="Sample volume in µL (default: 5.0)",
)
@click.option(
    "--logp-solvent",
    required=False,
    type=click.Choice(["octanol", "toluene", "cyclohexane", "chloroform"], case_sensitive=False),
    help="Solvent for logP protocol (required when --protocol is logp)",
)
def t3_gencsv(regi, pka, filter_file, sample_col, output, protocol, concentration, volume, logp_solvent):
    """
    Tool for generating experiment files for SiriusT3 instrument.
    Expects a registration ("regi") file with sample information, a pKa file with estimated pKas,
    a protocol, and an output location.
    Items from the regi file with matching items in the pKa file (and the filter file, if provided) will be
    used to generate experiment import files. These files will be written to the output location.
    Matching is based on the column named "sample", unless another name is provided with the --sample-col argument.
    The pKa file is expected to be in one of two formats:
        1) a "short" format with a column named "reformatted_pkas" that are formatted for the SiriusT3 instrumnet as comma-separated values, e.g.,
            "ACID,4.5,BASE,10.5"
    or  2) a "long" format with one row per pKa, and separate columns named "pka_value" and "pka_type"
    """
    # Validate that logp_solvent is provided when protocol is logp
    if protocol.name.lower() == "logp" and not logp_solvent:
        raise click.UsageError("--logp-solvent is required when --protocol is logp")

    click.echo(f"Generating {protocol} CSV for import")
    merged_df = generate_registration_pka_file(
        registration_csv=regi,
        pka_csv=pka,
        filter_file=filter_file,
        sample_col=sample_col,
        concentration_mM=concentration,
        volume_ul=volume,
    )
    buffer = StringIO(merged_df.to_csv(None, index=False))
    # Pass solvent parameter for logp protocol
    if protocol.name.lower() == "logp":
        formatter = protocol.value(input_csv=buffer, sample_id_col=sample_col, solvent=logp_solvent)
    else:
        formatter = protocol.value(input_csv=buffer, sample_id_col=sample_col)
    click.echo(f"Found {formatter.num_samples} samples with estimated pKa values.")
    formatter.generate_csv_files(output_dir=output)
