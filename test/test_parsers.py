import datetime
import pathlib

import pytest

from t3_chomper.logger import get_logger
from t3_chomper.parsers import (
    UVMetricPKaT3RParser,
    AssayCategory,
    PkaResult,
    PkaType,
    LogPT3RParser,
    LogPResult,
)

logger = get_logger(__name__)


@pytest.fixture
def pka_result_filename():
    """example of a pKa result file"""
    return r"test/data/fast_uv_OCNT-0000018-AQ-001.t3r"


@pytest.fixture
def logp_result_filename():
    """example of a logP result file"""
    return r"test/data/logp_OCNT-0000018-AQ-001_octanol.t3r"


def test_pka_parser(pka_result_filename):
    """Test UVMetricPKaT3RParser class"""

    x = UVMetricPKaT3RParser(pka_result_filename)

    # Inherited from base class
    assert x.EXPECTED_ASSAY_CATEGORY == AssayCategory.PKA == x.assay_category
    assert isinstance(x.filename, pathlib.Path)
    assert x.filename == pathlib.Path(pka_result_filename)
    assert x.assay_name == r"Fast UV psKa"
    assert isinstance(x.assay_datetime, datetime.datetime)
    assert x.assay_quality == "Good"
    assert x.sample_name == r"C:\Pion Data\pilot fragment_16\OCNT-0000018-AQ-001.xmol"

    # Pka-specific
    result_dict = x.result_dict
    assert isinstance(x.result_dict, dict)
    assert all(
        key in result_dict
        for key in [
            "filename",
            "sample",
            "assay_name",
            "pka_list",
            "std_list",
            "reformatted_pkas",
        ]
    )
    pka_results = x.pka_results
    assert len(pka_results) == 1
    result = pka_results[0]
    assert isinstance(result, PkaResult)
    assert result.value == 8.11591
    assert result.std == 0.203242

    predicted_pkas = x.predicted_pka
    assert len(predicted_pkas) == 1
    predicted_pka = predicted_pkas[0]
    assert predicted_pka.value == 8.23
    assert predicted_pka.pka_type == PkaType.BASE

    t3_formatted_results = x.t3_formatted_results
    assert isinstance(t3_formatted_results, str)
    assert t3_formatted_results == r"base,8.11591"


def test_logp_parser(logp_result_filename):
    """test LogPT3RParser class"""

    x = LogPT3RParser(logp_result_filename)
    assert x.assay_category == x.EXPECTED_ASSAY_CATEGORY == AssayCategory.LOGP
    result_dict = x.result_dict
    assert isinstance(result_dict, dict)
    assert all(
        key in result_dict
        for key in ["filename", "sample", "assay_name", "logp", "rmsd", "solvent"]
    )
    result = x.logp_result
    assert isinstance(result, LogPResult)
    assert result.value == 2.12231
    assert result.rmsd == 0.0516447
    assert x.logp_solvent == result.solvent == "Octanol"
