import logging
import pathlib

import pandas as pd

logger = logging.getLogger(__name__)


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


def generate_sirius_csv_import(
    input_csv: str,
    output_dir: str,
    pkas_col: str = "reformatted_pkas",
    sample_id_col: str = "batch_sample",
) -> None:
    """
    Generate a CSV import file for loading samples into a SeriusT3 instrument.

    Args:
        input_csv: input data file with compound IDs and estimated pKas
        output_dir: output dir for the generated CSV files
        pkas_col: name for the column containing the estimated pKas
        sample_id_col: name for column containing the sample names
    """

    df = pd.read_csv(input_csv)
    if pkas_col not in df.columns:
        raise ValueError(f"Column {pkas_col} not found in {input_csv}")
    missing_pkas_count = df[pkas_col].isna().sum()
    if missing_pkas_count:
        missing_row_ids = df[df[pkas_col].isna()][sample_id_col]
        raise ValueError(
            f"Input file has {missing_pkas_count} missing estimated pKas: {missing_row_ids}"
        )

    output_path = pathlib.Path(output_dir)
    output_path.mkdir()

    # Split into sets of 47 samples per tray
    tray_dfs = [df[i : i + 47] for i in range(0, df.shape[0], 47)]
    for idx, tray_df in enumerate(tray_dfs):
        outstr = "SCHEDULEIMPORTCSV\n\n"
        lines = []
        for row in tray_df.itertuples():
            lines.append(
                ",".join(
                    [
                        f"{getattr(row, sample_id_col)}",
                        f"{getattr(row, pkas_col).rstrip(',')}",
                        f"""SYM,{getattr(row, "well")}""",
                        f"""MW,{getattr(row, "mw")}""",
                    ]
                )
            )
        outstr += "\n".join(lines)
        outstr += f"\n\nTRAY,{output_dir}_{idx}\n"

        # First experiment is to run a blank for calibration
        outstr += "Fast UV Buffer Calib MeOH\n"

        lines = []
        for row in tray_df.itertuples():
            sample_name = getattr(row, sample_id_col)
            # TODO: should we specify a well location here?
            lines.append(
                ",".join(
                    [
                        "Fast UV psKa",
                        f"title,pka of {sample_name}",
                        f"{sample_name}",
                        f"{sample_name},1",
                        f"""fw,{getattr(row, "fw")}""",
                        "volume,0.005",
                        "Concentration,10",
                        "DMSO,1",
                    ]
                )
            )
        outstr += "\n".join(lines)

        output_filename = output_path / f"tray_{idx}.csv"
        with open(output_filename, "w") as fout:
            fout.write(outstr)
        logger.info(f"Wrote to {output_filename}")
    logger.info(f"Wrote {len(tray_dfs)} output files.")
