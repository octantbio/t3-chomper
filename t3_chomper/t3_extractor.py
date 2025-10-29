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
        """
        Args:
            path: either string or path pointing to a single file or directory of t3r files
        """
        self.path = Path(path)
        self.num_files = None
        self.rows = []
        self.failed_filenames = []

        if self.path.is_dir():
            self._t3_files = list(self.path.glob("*.t3r"))
            if not self._t3_files:
                raise FileNotFoundError(f"No .t3r files found in directory: {path}")
            self.num_files = len(self._t3_files)
            logger.info(f"Found {self.num_files} t3r results files.")
        else:
            self._t3_files = [self.path]
            self.num_files = 1
            logger.info(f"Found 1 t3r result file.")

    @property
    def num_succeeded(self) -> int:
        """
        Number of successfully parsed files
        """
        return len(self.rows)

    @property
    def num_failed(self) -> int:
        """
        Number of filenames that failed parsing
        """
        return len(self.failed_filenames)

    def parse_pka_files(self) -> None:
        """
        Parse pKa result data files and return a dataframe of parsed results
        """
        for file in self._t3_files:
            logger.debug(f"Parsing T3R XML file: {file}")
            try:
                pka_parser = UVMetricPKaT3RParser(file)
                # Get results as list of dict objects per pKa
                results_list = pka_parser.result_list
                self.rows.extend(results_list)
            except Exception as e:
                logger.error(f"Error parsing data: {e}")
                self.failed_filenames.append(file)

    def parse_logp_files(self) -> None:
        """
        Parse logp result data files and return a dataframe of parsed results
        """
        for file in self._t3_files:
            logger.debug(f"Parsing T3R XML file: {file}")
            try:
                logp_parser = LogPT3RParser(file)
                # Get logp result as a dict object
                result = logp_parser.result_dict
                self.rows.append(result)
            except Exception as e:
                logger.error(f"Error parsing data: {e}")
                self.failed_filenames.append(file)

    def get_results_df(self) -> pd.DataFrame:
        """
        Return results as a dataframe
        """
        if len(self.rows) == 0:
            logger.error(f"No parsed results")
        return pd.DataFrame(self.rows)

    def write_results_csv(self, filename: Union[str, Path]) -> None:
        """
        Write parsed results to csv
        Args:
            filename: filename for the output file
        """
        df = self.get_results_df()
        df.to_csv(filename, index=False)

    def write_failed_csv(self, filename: Union[str, Path]) -> None:
        """
        Write a csv file with a column of filenames which failed to parse
        Args:
            filename: filename for the failed filenames file
        """
        if len(self.failed_filenames) == 0:
            logger.info(f"No files failed to parse")
        df = pd.DataFrame({"failed_filenames": self.failed_filenames})
        df.to_csv(filename, index=False)


@click.command()
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, readable=True),
    default=None,
)
@click.option(
    "--output",
    type=click.Path(exists=False, file_okay=True),
)
@click.option(
    "--protocol", required=True, type=click.Choice(AssayCategory, case_sensitive=False)
)
def t3_extract(path, output, protocol):
    click.echo(f"Extracting data from t3r files.")
    extractor = FileOrPathExtractor(path=path)

    if protocol == AssayCategory.PKA:
        extractor.parse_pka_files()
    elif protocol == AssayCategory.LOGP:
        extractor.parse_logp_files()
    else:
        raise ValueError(f"Unknown Assay category: {protocol}")

    if output:
        logger.info(f"Finished parsing, writing to {output}")
        extractor.write_results_csv(output)

        failed_filenames_loc = Path(output).parent / "failed_filenames.csv"
        extractor.write_failed_csv(failed_filenames_loc)
    else:
        logger.info(f"No output file provided, writing to stdout.")
        df = extractor.get_results_df()
        click.echo(df.to_csv(index=False))
        if extractor.num_failed > 0:
            logger.error(f"{extractor.num_failed} files failed to parse.")
