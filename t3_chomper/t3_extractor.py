"""CLI for extracting data from t3r files."""

import glob
from pathlib import Path
from typing import Union

import click
import pandas as pd

from t3_chomper.extractors import UVMetricPKaT3RExtractor
from t3_chomper.logger import get_logger

logger = get_logger(__name__)


def parse_t3_pka_xml(file: Union[str, Path]) -> tuple:
    """
    Read XML file from the Sirus T3 machine and extract pKa data.

    Returns:
        Tuple of (pka, stdev, ionic_strength, temp)
    """
    extractor = UVMetricPKaT3RExtractor(file)

    pka = extractor.mean_pka_values
    stdev = extractor.mean_pka_std_values
    ionic_strength = extractor.mean_pka_ionic_strengths
    temp = extractor.mean_pka_temperatures

    return pka, stdev, ionic_strength, temp


def parse_pkas(
    t3_dir: Union[str, None] = None, t3_file: Union[str, None] = None
) -> pd.DataFrame:
    """
    Parse one or multiple .t3 files from directory or single file into a DataFrame.

    Only one of t3_dir or t3_file must be provided.
    """
    if (t3_dir is None and t3_file is None) or (t3_dir and t3_file):
        raise ValueError("Provide either t3_dir or t3_file, but not both.")

    if t3_dir:
        t3_files = glob.glob(f"{t3_dir}/*.t3r")
        if not t3_files:
            raise FileNotFoundError(f"No .t3r files found in directory: {t3_dir}")
    else:
        t3_files = [t3_file]

    rows = []
    for file in t3_files:
        logger.debug(f"Parsing T3 XML file: {file}")
        try:
            pka, stdev, ionic_strength, temp = parse_t3_pka_xml(file)
        except Exception as e:
            logger.error(f"Error parsing file {file}: {e}")
            continue

        rows.append(
            {
                "file": Path(file).name,
                "pka": pka,
                "stdev": stdev,
                "ionic_strength": ionic_strength,
                "temperature": temp,
            }
        )

    df = pd.DataFrame(rows)
    return df


@click.command()
@click.option(
    "--t3-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    default=None,
    help="Directory containing .t3 files",
)
@click.option(
    "--t3-file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    default=None,
    help="Single .t3 file to parse",
)
@click.option(
    "--output_csv",
    type=click.Path(exists=False, file_okay=True),
    default="pka_results.csv",
)
def pka(t3_dir, t3_file, output_csv):
    """
    CLI entry point for parsing T3 pKa XML files and exporting to CSV.
    """
    logger.info("Running T3 pKa parsing")
    df = parse_pkas(t3_dir, t3_file)
    logger.info(f"Finished parsing, writing to {output_csv}")
    df.to_csv(output_csv, index=False)


if __name__ == "__main__":
    pka()
