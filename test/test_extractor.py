import pathlib

import pandas as pd

from test.fixtures import pka_result_filename, logp_result_filename
from t3_chomper.t3_extractor import FileOrPathExtractor


def test_pka_extractor(pka_result_filename):
    x = FileOrPathExtractor(pka_result_filename)
    assert isinstance(x._t3_files, list)
    assert len(x._t3_files) == 1
    assert x._t3_files[0] == pathlib.Path(pka_result_filename)
    x.parse_pka_files()
    df = x.get_results_df()
    assert x.num_succeeded == 1
    assert x.num_failed == 0
    assert isinstance(df, pd.DataFrame)
    assert all(
        col in df.columns
        for col in [
            "sample",
            "filename",
            "assay_name",
            "assay_quality",
            "pka_number",
            "pka_type",
            "pka_std",
            "pka_ionic_strength",
            "pka_temperature",
        ]
    )
    assert len(df) == 1
    assert df.loc[0, "pka_type"] == "base"
    assert df.loc[0, "pka_number"] == 1
    assert df.loc[0, "pka_value"] == 8.11591
    assert df.loc[0, "pka_std"] == 0.203242


def test_logp_extractor(logp_result_filename):
    x = FileOrPathExtractor(logp_result_filename)
    assert isinstance(x._t3_files, list)
    assert len(x._t3_files) == 1
    assert x._t3_files[0] == pathlib.Path(logp_result_filename)
    x.parse_logp_files()
    df = x.get_results_df()
    assert isinstance(df, pd.DataFrame)
    assert x.num_succeeded == 1
    assert x.num_failed == 0
    assert all(
        col in df.columns
        for col in [
            "sample",
            "filename",
            "assay_name",
            "logp",
            "rmsd",
            "solvent",
        ]
    )
    assert len(df) == 1
    assert df.loc[0, "logp"] == 2.12231
    assert df.loc[0, "rmsd"] == 0.0516447
    assert df.loc[0, "solvent"] == "Octanol"
