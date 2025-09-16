import pandas as pd


def generate_registration_pka_file(registration_csv: str, pka_csv: str) -> pd.DataFrame:
    """
    From a CSV of registration data and a CSV of estimated pKa data, return a merged dataframe

    args:
        registration_csv: registration data file. Expects compounds to be annotated with "ID" column
        pka_csv: pKa estimate data file. Expected compounds to be annotated with a "vendor_id" column, and
            pKa estimates formatted for Pion Sirius T3 input files under a column named "reformatted_pkas"
    """
    regi_df = pd.read_csv(registration_csv)
    pka_df = pd.read_csv(pka_csv, usecols=["vendor_id", "reformatted_pkas"])

    merged_df = pd.merge(regi_df, pka_df, how="left", left_on="ID",
                         right_on="vendor_id").drop(columns=["vendor_id"])

    missing_rows = merged_df["reformatted_pkas"].isna().sum()
    if missing_rows:
        missing_row_ids = merged_df[merged_df["reformatted_pkas"].isna()]["ID"]
        raise ValueError(f"Some rows have missing data: {missing_row_ids}")

    return merged_df