import enum
import pathlib

import pandas as pd

from t3_chomper.logger import get_logger

logger = get_logger(__name__)


def convert_long_pka_df(
    long_df: pd.DataFrame,
    id_col: str = "vendor_id",
    pka_col: str = "pka_value",
    pka_type_col: str = "pka_type",
    reformatted_pka_col: str = "reformatted_pkas",
) -> pd.DataFrame:
    """
    Convert long-format pKa data file to short-format
    long-format data files have multiple rows for each pKa, with columns like 'pka_number', 'pka_type', 'pka_value'
    short-format has one row per compound and a column containing a string representation of multiple pKas
    The string representation of multiple pKas has the format:
        <type1>,<value1>,<type2>,<value2>,...
    Where the types are either ACID or BASE and the multiple elements should be sorted by increasing value.

    Args:
        long_df: long-format pKa file, i.e. multiple pKas on multiple lines
        id_col: column name with compound name
        pka_col: column name with pKa value
        pka_type_col: column name with pKa type (acid or base)
        reformatted_pka_col: column name to generate with reformatted pKa string
    """
    for col in [id_col, pka_col, pka_type_col]:
        if col not in long_df.columns:
            raise ValueError(f"Missing expected column {col} ")
    # Sort by compound and ascending pKa value
    long_df.sort_values([id_col, pka_col], inplace=True)
    # Aggregate to one row per compound, with a list for pKa types and values
    agg_df = long_df.groupby(id_col)[[pka_type_col, pka_col]].agg(list).reset_index()
    # Generate reformatted pKa string
    agg_df[reformatted_pka_col] = agg_df.apply(
        lambda x: ",".join(
            f"{t.upper()},{v}"
            for t, v in zip(getattr(x, pka_type_col), getattr(x, pka_col))
        ),
        axis=1,
    )
    return agg_df


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
    regi_required_columns = [
        registration_id_col,
        "Registry Number",
        "Batch Name",
        "Well",
        "MW",
    ]
    for col in regi_required_columns:
        if col not in regi_df.columns:
            raise ValueError(
                f"Expected column {col} is missing in {registration_csv}"
            )
    if "batch_sample" not in regi_df.columns:
        regi_df["batch_sample"] = regi_df.apply(
            lambda x: f"""{x["Registry Number"]}-{x["Batch Name"]}""", axis=1
        )

    pka_df = pd.read_csv(pka_csv)
    if pka_id_col not in pka_df.columns:
        raise ValueError(f"Expected column {pka_id_col} is missing in {pka_csv}")

    # If the pKa data file is in the long-format with one row per pKa, then try to reformat
    # to generate a 'short-format' pKa file with one row per compound
    if pka_pkas_col not in pka_df.columns:
        pka_df = convert_long_pka_df(pka_df, id_col=pka_id_col)

    pka_df = pka_df[[pka_id_col, pka_pkas_col]].rename(
        columns={pka_id_col: registration_id_col}
    )

    # left join on regi file, unmatched rows will have null pKa values
    merged_df = pd.merge(regi_df, pka_df, how="left", on=registration_id_col)

    # Warn if there are rows with unmatched pKa values
    missing_row_count = merged_df[pka_pkas_col].isna().sum()
    if missing_row_count:
        missing_row_ids = merged_df[merged_df[pka_pkas_col].isna()][registration_id_col]
        logger.warning(
            f"{missing_row_count} rows have missing pKa data and will be dropped: {missing_row_ids}"
        )
    # Drop rows with no pKa data
    merged_df.dropna(subset=pka_pkas_col, inplace=True)

    return merged_df


class SiriusT3CSVGenerator:
    """
    Abstract class used to generate CSV import file(s) for loading samples into a SiriusT3 instrument.
    Subclasses will have different implementations for writing the experimental sections in the generated CSV files.

    Args:
        input_csv: input data file with compound IDs and estimated pKas
        pkas_col: name for the column containing the estimated pKas
        sample_id_col: name for column containing the sample names
        fw_col: name for column with formula weights
        mg_col: name for column with mass in mg
        well_col: name for column with well position
        mw_col: name for column with molecular weight
    """

    SAMPLES_PER_TRAY = 48

    def __init__(
        self,
        input_csv: str,
        pkas_col: str = "reformatted_pkas",
        sample_id_col: str = "batch_sample",
        fw_col: str = "fw",
        mg_col: str = "mg",
        well_col: str = "well",
        mw_col: str = "mw",
    ):
        self._input_csv = input_csv
        self._pkas_col = pkas_col
        self._sample_id_col = sample_id_col
        self._fw_col = fw_col
        self._mg_col = mg_col
        self._well_col = well_col
        self._mw_col = mw_col

        self._df = self._load_input_file()

    @property
    def input_csv(self) -> str:
        return self._input_csv

    def _load_input_file(self) -> pd.DataFrame:
        df = pd.read_csv(self._input_csv)
        df.rename(columns=str.lower, inplace=True)
        for col in [self._pkas_col, self._sample_id_col, self._well_col, self._mw_col]:
            if col not in df.columns:
                raise ValueError(f"""Column "{col}" not found in {self._input_csv}""")
        missing_pkas_count = df[self._pkas_col].isna().sum()
        if missing_pkas_count:
            missing_row_ids = df[df[self._pkas_col].isna()][self._sample_id_col]
            raise ValueError(
                f"Input file has {missing_pkas_count} missing estimated pKas: {missing_row_ids}"
            )
        return df

    def generate_header_section(self) -> str:
        return "ScheduleImportCsv\n\n"

    def generate_sample_section(self, sample_df: pd.DataFrame) -> str:
        """Generate section of the SiriusT3 CSV import file with Sample information"""
        lines = []
        for row in sample_df.itertuples():
            lines.append(
                ",".join(
                    [
                        f"{getattr(row, self._sample_id_col)}",
                        f"{getattr(row, self._pkas_col).rstrip(',')}",
                        f"""SYM,{getattr(row, self._well_col)}""",
                        f"""MW,{getattr(row, self._mw_col)}""",
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
            tray_name = f"""{output_dir.strip("/")}_{idx}"""
            outstr = self.generate_header_section()
            outstr += self.generate_sample_section(tray_df)
            outstr += f"""\n\nTRAY,{tray_name}\n"""
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


class UVMetricPSKAGenerator(SiriusT3CSVGenerator):
    SAMPLES_PER_TRAY = 24

    def generate_experiment_section(self, sample_df: pd.DataFrame) -> str:
        """
        Generate experiment section for a UV-metric psKa experiment tray.
        Tray has 24 samples, a calibration assay is automatically added before each sample.
        This assumes that each sample is at 0.005 mL and 10 mM in pure DMSO
        """
        lines = []
        for row in sample_df.itertuples():
            sample_name = getattr(row, self._sample_id_col)
            lines.append(
                ",".join(
                    [
                        "UV-metric psKa",
                        f"title,UV-metric psKa of {sample_name} by volume",
                        f"{sample_name}",  # sample
                        f"{sample_name},1",  # component and stoichiometry
                        "volume,0.005",
                        "Concentration,10",
                        "DMSO,1",
                    ]
                )
            )
        return "\n".join(lines)


class PHMetricPSKAGenerator(SiriusT3CSVGenerator):
    SAMPLES_PER_TRAY = 24

    def generate_experiment_section(self, sample_df: pd.DataFrame) -> str:
        """
        Generate experiment section for a pH-metric psKa experiment tray.
        Tray has 24 samples, with a "Clean Up" step after every sample.
        Samples are solid powder, so mg is specified.
        """
        lines = []
        for row in sample_df.itertuples():
            sample_name = getattr(row, self._sample_id_col)
            lines.append(
                ",".join(
                    [
                        "pH-metric psKa",
                        f"title,pH-metric psKa of {sample_name} by weight",
                        f"{sample_name}",  # sample
                        f"{sample_name},1",  # component and stoichiometry
                        f"""fw,{getattr(row, self._fw_col)}""",
                        f"""mg,{getattr(row, self._mg_col)}""",
                    ]
                )
            )
            lines.append("Clean Up")
        return "\n".join(lines)


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
                        f"""fw,{getattr(row, self._fw_col)}""",
                        f"""mg, {getattr(row, self._mg_col)}""",
                    ]
                )
            )
            lines.append("Clean Up")
            lines.append("Clean Up")
        return "\n".join(lines)


class TrayFormat(enum.Enum):
    """
    Enum of defined tray formats
    """

    FastUVPSKA = FastUVPSKAGenerator
    PHMetric = PHMetricPSKAGenerator
    UVMetric = UVMetricPSKAGenerator
    LogP = LogPGenerator
