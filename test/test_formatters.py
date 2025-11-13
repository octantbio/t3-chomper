from io import StringIO

import pandas as pd
import pytest

from t3_chomper.formatters import convert_long_pka_df, LogPGenerator


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


@pytest.fixture
def logp_test_data():
    """Test data for LogP generator"""
    return (
        "sample,well,mw,fw,mg,reformatted_pkas\n"
        "cpd1,A1,250.5,250.5,5.0,ACID,2.5\n"
        "cpd2,A2,300.2,300.2,5.0,BASE,9.3\n"
    )


@pytest.mark.parametrize("solvent", ["octanol", "toluene", "cyclohexane", "chloroform"])
def test_logp_generator_solvent(logp_test_data, solvent):
    """
    Test that LogPGenerator correctly uses the provided solvent in generated experiment lines
    """
    data = StringIO(logp_test_data)
    generator = LogPGenerator(input_csv=data, solvent=solvent)

    # Get the experiment section
    experiment_section = generator.generate_experiment_section(generator._df)

    # Verify the solvent appears in the generated lines
    assert f"pH-metric medium logP {solvent}" in experiment_section

    # Verify it appears for each sample (2 samples in test data)
    lines = experiment_section.split("\n")
    solvent_lines = [line for line in lines if f"pH-metric medium logP {solvent}" in line]
    assert len(solvent_lines) == 2


def test_logp_generator_default_solvent(logp_test_data):
    """
    Test that LogPGenerator has a default solvent value when not specified
    """
    data = StringIO(logp_test_data)
    # Create generator without specifying solvent (should use default "none")
    generator = LogPGenerator(input_csv=data)

    # Verify the default solvent is used
    experiment_section = generator.generate_experiment_section(generator._df)
    assert "pH-metric medium logP none" in experiment_section
