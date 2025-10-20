import pytest


@pytest.fixture
def pka_result_filename():
    """example of a pKa result file"""
    return r"test/data/fast_uv_OCNT-0000018-AQ-001.t3r"


@pytest.fixture
def logp_result_filename():
    """example of a logP result file"""
    return r"test/data/logp_OCNT-0000018-AQ-001_octanol.t3r"
