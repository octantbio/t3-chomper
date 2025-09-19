import pathlib

import pandas as pd

from t3_chomper.logger import get_logger

logger = get_logger(__name__)


def generate_registration_pka_file(
    registration_csv: str,
    pka_csv: str,
    registration_id_col: str = "ID",
    pka_id_col: str = "vendor_id",
    pka_pkas_col: str = "reformatted_pkas",
) -> pd.DataFrame:
    """
    From a CSV of registration data and a CSV of estimated pKa data, return a merged dataframe

    args:
        registration_csv: registration data file. Expects compounds to be annotated with "ID" column
        pka_csv: pKa estimate data file. Expected compounds to be annotated with a "vendor_id" column, and
            pKa estimates formatted for Pion Sirius T3 input files under a column named "reformatted_pkas"
        registration_id_col: name of the column in the registration file with compound IDs
        pka_id_col: name of the column in the pKa data file with compound IDs
        pka_pkas_col: name of the column in the pKa data file with pKa data

    Returns:
        Merged dataframe with columns from the registration_csv and the estimated pKa data from the pKa data file
    """

    regi_df = pd.read_csv(registration_csv)
    if registration_id_col not in regi_df.columns:
        raise ValueError(
            f"Expected column {registration_id_col} is missing in {registration_csv}"
        )

    pka_df = pd.read_csv(pka_csv)
    for col in [pka_id_col, pka_pkas_col]:
        if col not in pka_df.columns:
            raise ValueError(f"Expected column {col} is missing in {pka_csv}")

    pka_df = pka_df[[pka_id_col, pka_pkas_col]].rename(
        columns={pka_id_col: registration_id_col}
    )

    merged_df = pd.merge(regi_df, pka_df, how="left", on=registration_id_col)

    missing_row_count = merged_df[pka_pkas_col].isna().sum()
    if missing_row_count:
        missing_row_ids = merged_df[merged_df[pka_pkas_col].isna()][registration_id_col]
        raise ValueError(
            f"{missing_row_count} rows have missing data: {missing_row_ids}"
        )

    return merged_df


class SiriusT3CSVGenerator:
    """
    Abstract class used to generate CSV import file(s) for loading samples into a SeriusT3 instrument.
    Subclasses will have different implementations for writing the experimental sections in the generated CSV files.

    Args:
        input_csv: input data file with compound IDs and estimated pKas
        pkas_col: name for the column containing the estimated pKas
        sample_id_col: name for column containing the sample names

    """

    SAMPLES_PER_TRAY = 48

    def __init__(
        self,
        input_csv: str,
        pkas_col: str = "reformatted_pkas",
        sample_id_col: str = "batch_sample",
    ):
        self._input_csv = input_csv
        self._pkas_col = pkas_col
        self._sample_id_col = sample_id_col
        self._df = self._load_input_file()

    @property
    def input_csv(self) -> str:
        return self._input_csv

    def _load_input_file(self) -> pd.DataFrame:
        df = pd.read_csv(self._input_csv)
        if self._pkas_col not in df.columns:
            raise ValueError(f"Column {self._pkas_col} not found in {self._input_csv}")
        missing_pkas_count = df[self._pkas_col].isna().sum()
        if missing_pkas_count:
            missing_row_ids = df[df[self._pkas_col].isna()][self._sample_id_col]
            raise ValueError(
                f"Input file has {missing_pkas_count} missing estimated pKas: {missing_row_ids}"
            )
        return df

    def generate_header_section(self) -> str:
        return "ScheduleImportCSV\n\n"

    def generate_sample_section(self, sample_df: pd.DataFrame) -> str:
        """Generate section of the SiriusT3 CSV import file with Sample information"""
        lines = []
        for row in sample_df.itertuples():
            lines.append(
                ",".join(
                    [
                        f"{getattr(row, self._sample_id_col)}",
                        f"{getattr(row, self._pkas_col).rstrip(',')}",
                        f"""SYM,{getattr(row, "well")}""",
                        f"""MW,{getattr(row, "mw")}""",
                    ]
                )
            )
        return "\n".join(lines)

    def generate_experiment_section(self, sample_df: pd.DataFrame) -> str:
        raise NotImplementedError

    @property
    def num_samples(self):
        """Total number of samples in input"""
        return self._df.shape[0]

    def _get_split_dfs(self) -> list[pd.DataFrame]:
        """Split samples in input into chunks for each tray"""
        return [
            self._df.iloc[i : i + self.SAMPLES_PER_TRAY]
            for i in range(0, self.num_samples, self.SAMPLES_PER_TRAY)
        ]

    def generate_csv_files(self, output_dir) -> None:
        """Generate CSV files for import"""

        output_path = pathlib.Path(output_dir)
        output_path.mkdir()

        for idx, tray_df in enumerate(self._get_split_dfs()):
            outstr = self.generate_header_section()
            outstr += self.generate_sample_section(tray_df)
            outstr += f"""\n\nTRAY,{output_dir.strip("/")}_{idx}\n"""
            outstr += self.generate_experiment_section(tray_df)

            output_filename = output_path / f"tray_{idx}.csv"
            with open(output_filename, "w") as fout:
                fout.write(outstr)
            logger.info(f"Wrote to {output_filename}")


class FastUVPSKAGenerator(SiriusT3CSVGenerator):
    SAMPLES_PER_TRAY = 47

    def generate_experiment_section(self, sample_df: pd.DataFrame) -> str:
        """
        Generate experiment section for Fast UV pKa experiment.
        This does one calibration experiment "Fast UV Buffer Calib MeOH" per plate,
        and then "Fast UV psKa" for 47 samples, each at 0.005 mL and 10 mM in pure DMSO
        """

        lines = []
        for row in sample_df.itertuples():
            sample_name = getattr(row, self._sample_id_col)
            # TODO: should we specify a well location here? What about FW?
            lines.append(
                ",".join(
                    [
                        "Fast UV psKa",
                        f"title,pka of {sample_name}",
                        f"{sample_name}",
                        f"{sample_name},1",
                        "volume,0.005",
                        "Concentration,10",
                        "DMSO,1",
                    ]
                )
            )
        return "Fast UV Buffer Calib MeOH\n" + "\n".join(lines)


class LogPGenerator(SiriusT3CSVGenerator):
    SAMPLES_PER_TRAY = 16

    def generate_experimental_section(self, sample_df: pd.DataFrame) -> str:
        """
        Generate the experimental section for the "pH-metric medium logP octanol" template.
        This has 16 samples with 2x cleanup steps in between samples in each plate
        """
        lines = []
        for row in sample_df.itertuples():
            sample_name = getattr(row, self._sample_id_col)
            lines.append(
                ",".join(
                    [
                        "pH-metric medium logP octanol",
                        f"title,logP of {sample_name}",
                        f"{sample_name}",
                        f"{sample_name},1",
                        f"""fw,{getattr(row, "fw")}""",
                        f"""mg, {getattr(row, "mg")}""",
                    ]
                )
            )
            lines.append("Clean Up")
            lines.append("Clean Up")
        return "\n".join(lines)
