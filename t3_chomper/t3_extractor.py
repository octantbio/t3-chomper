"""CLI for extracting data from t3r files."""

import glob
from pathlib import Path
from typing import Union

import click
import pandas as pd

from t3_chomper.extractors import (
    UVMetricPKaT3RExtractor,
    LogPT3RExtractor,
    AssayCategory,
)
from t3_chomper.logger import get_logger

logger = get_logger(__name__)


class FileOrPathExtractor:
    """
    Class to extract data from one or more t3r result files.
    """

    def __init__(
        self,
        t3_dir: Union[str, None] = None,
        t3_file: Union[str, None] = None,
    ):
        if (t3_dir is None and t3_file is None) or (t3_dir and t3_file):
            raise ValueError("Provide either t3_dir or t3_file, but not both.")

        if t3_dir:
            self._t3_files = glob.glob(f"{t3_dir}/*.t3r")
            if not self._t3_files:
                raise FileNotFoundError(f"No .t3r files found in directory: {t3_dir}")
        else:
            self._t3_files = [t3_file]

    def _parse_files(self, assay_category: AssayCategory) -> pd.DataFrame:
        """ """
        rows = []
        for file in self._t3_files:
            logger.debug(f"Parsing T3R XML file: {file}")
            if assay_category == AssayCategory.PKA:
                pka_parser = UVMetricPKaT3RExtractor(file)
                results = pka_parser.result_dict
            elif assay_category == AssayCategory.LOGP:
                logp_parser = LogPT3RExtractor(file)
                results = logp_parser.result_dict
            else:
                raise ValueError(f"Unknown assay category: {assay_category}")
            results["file"] = Path(file).name
            rows.append(results)
        df = pd.DataFrame(rows)
        return df

    def parse_pka_files(self):
        return self._parse_files(AssayCategory.PKA)

    def parse_logp_files(self):
        return self._parse_files(AssayCategory.LOGP)


@click.group()
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
def t3r_extract():
    click.echo(f"Extracting data from t3r files.")


@t3r_extract.command()
def pka(t3_dir, t3_file, output_csv):
    """
    Parse T3R pKa XML files and export to CSV.
    """
    logger.info("Running T3 pKa parsing")
    extractor = FileOrPathExtractor(t3_dir=t3_dir, t3_file=t3_file)
    df = extractor.parse_pka_files()
    logger.info(f"Finished parsing, writing to {output_csv}")
    df.to_csv(output_csv, index=False)


@t3r_extract.command()
def logp(t3_dir, t3_file, output_csv):
    """
    Parse T3R logp XML files and export to CSV.
    """
    logger.info("Running T3 logp parsing")
    extractor = FileOrPathExtractor(t3_dir=t3_dir, t3_file=t3_file)
    df = extractor.parse_logp_files()
    logger.info(f"Finished parsing, writing to {output_csv}")
    df.to_csv(output_csv, index=False)


if __name__ == "__main__":
    pass
