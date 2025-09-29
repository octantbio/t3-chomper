"""CLI for extracting data from t3r files."""

from pathlib import Path
from typing import Union

import click
import pandas as pd

from t3_chomper.parsers import (
    UVMetricPKaT3RParser,
    LogPT3RParser,
    AssayCategory,
)
from t3_chomper.logger import get_logger

logger = get_logger(__name__)


class FileOrPathExtractor:
    """
    Class to extract data from one or more t3r result files.
    """

    def __init__(self, path: Union[str, Path]):
        path = Path(path)
        if path.is_dir():
            self._t3_files = list(path.glob("*.t3r"))
            if not self._t3_files:
                raise FileNotFoundError(f"No .t3r files found in directory: {path}")
            num_files = len(self._t3_files)
            logger.info(f"Found {num_files} t3r results files.")
        else:
            self._t3_files = [path]
            logger.info(f"Found 1 t3r result file.")

    def _parse_files(self, assay_category: AssayCategory) -> pd.DataFrame:
        """ """
        rows = []
        for file in self._t3_files:
            logger.debug(f"Parsing T3R XML file: {file}")
            if assay_category == AssayCategory.PKA:
                pka_parser = UVMetricPKaT3RParser(file)
                results = pka_parser.result_dict
            elif assay_category == AssayCategory.LOGP:
                logp_parser = LogPT3RParser(file)
                results = logp_parser.result_dict
            else:
                raise ValueError(f"Unknown assay category: {assay_category}")
            rows.append(results)
        df = pd.DataFrame(rows)
        return df

    def parse_pka_files(self):
        return self._parse_files(AssayCategory.PKA)

    def parse_logp_files(self):
        return self._parse_files(AssayCategory.LOGP)


@click.command()
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, readable=True),
    default=None,
)
@click.option(
    "--output",
    type=click.Path(exists=False, file_okay=True),
    default="t3r_results.csv",
)
@click.option(
    "--protocol", required=True, type=click.Choice(AssayCategory, case_sensitive=False)
)
def t3_extract(path, output, protocol):
    click.echo(f"Extracting data from t3r files.")
    extractor = FileOrPathExtractor(path=path)
    if protocol == AssayCategory.PKA:
        df = extractor.parse_pka_files()
    elif protocol == AssayCategory.LOGP:
        df = extractor.parse_logp_files()
    else:
        raise ValueError(f"Unknown Assay category: {protocol}")
    logger.info(f"Finished parsing, writing to {output}")
    df.to_csv(output, index=False)
