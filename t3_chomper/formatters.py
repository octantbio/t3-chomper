import pandas as pd


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
