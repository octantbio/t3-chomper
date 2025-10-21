from io import StringIO

import pandas as pd
import pytest

from t3_chomper.formatters import convert_long_pka_df


@pytest.fixture
def long_pka_data():
    return (
        "compound,pka_number,pka_type,pka_estimate,pka_sd\n"
        "cpd1,1,acid,2.05,0.05\n"
        "cpd1,2,base,6.75,0.03\n"
    )


def test_convert_long_to_short(long_pka_data):
    """
    Test converting a long-format pKa data file with one row per pKa
    to a short-format pKa datafile with one row per compound.
    """
    data = StringIO(long_pka_data)
    df_long = pd.read_csv(data)
    df_short = convert_long_pka_df(df_long, id_col="compound", pka_col="pka_estimate")
    assert len(df_long) == 2
    assert len(df_short) == 1
    reformatted_pkas = df_short.reformatted_pkas.iloc[0]
    assert reformatted_pkas == "ACID,2.05,BASE,6.75"
