from datetime import datetime
import enum
from dataclasses import dataclass
from functools import cached_property
import re

import xmltodict

from t3_chomper.logging import get_logger

logger = get_logger(__name__)

## TODO:
## - What happens with multiple Pkas? Can I get an example?
## - How to ensure the right logP
## - What other values do we want to extract from result files?


class CaseInsensitiveStrEnum(enum.StrEnum):
    "Enum that lets us refer to elements in a case-insensitive way"

    @classmethod
    def _missing_(cls, value):
        for member in cls:
            value = str(value).lower()
            if member.value == value:
                return member


class AssayCategory(CaseInsensitiveStrEnum):
    "Assay categories that we consider"

    NULL = enum.auto()
    PKA = enum.auto()
    LOGP = enum.auto()


class PkaType(CaseInsensitiveStrEnum):
    "Possible pKa types"

    ACID = enum.auto()
    BASE = enum.auto()


@dataclass
class PkaResult:
    "Container for a single pKa result or prediction"

    value: float
    std: float | None
    pka_type: PkaType
    source: str


@dataclass
class LogPResult:
    "Container for a single logP result"

    value: float
    rmsd: float


def get_assay_category(filename: str) -> AssayCategory:
    "Utility function to quickly get the assay category for a provided t3r file"

    with open(filename) as fin:
        res = re.findall(r"<Category>(\w+)</Category>", fin.read())
    if len(res) == 1:
        return AssayCategory(res[0])
    else:
        raise ValueError("Could not determine assay category")


class BaseT3RExtractor:
    """
    Base class for extracting data from T3R files.
    Subclasses can be defined for specific experimental protocols.
    This base class defines properties common to all t3r result files.
    """

    EXPECTED_ASSAY_CATEGORY = AssayCategory.NULL

    def __init__(self, filename: str) -> None:
        self._filename = filename
        self._doc: dict = {}
        self._load_document()

        if self.assay_category != self.EXPECTED_ASSAY_CATEGORY:
            raise ValueError("Input file is not the expected assay type")

    def _load_document(self):
        with open(self.filename, "rb") as fin:
            self._doc = xmltodict.parse(fin)
            logger.info(f"Loaded {self.filename}")

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def assay_name(self) -> str:
        return self._doc["DirectControlAssayResultsFile"]["Summary"]["AssayName"]

    @property
    def assay_datetime(self) -> datetime:
        return self._doc["DirectControlAssayResultsFile"]["Summary"]["StartTime"]

    @property
    def assay_category(self) -> AssayCategory:
        val = self._doc["DirectControlAssayResultsFile"]["AssayData"]["AssayTemplate"][
            "Category"
        ]
        return AssayCategory(val)

    @property
    def assay_quality(self) -> str:
        return self._doc["DirectControlAssayResultsFile"]["ProcessedData"][
            "AssayQuality"
        ]["Quality"]

    @property
    def sample_name(self) -> str:
        return self._doc["DirectControlAssayResultsFile"]["Summary"]["SampleName"]


class UVMetricPKaT3RExtractor(BaseT3RExtractor):
    """
    Class to handle results file from pKa Experiment
    """

    EXPECTED_ASSAY_CATEGORY = AssayCategory.PKA

    @cached_property
    def _mean_dpas_result(self) -> dict:
        try:
            return self._doc["DirectControlAssayResultsFile"]["ProcessedData"][
                "FastDpasMeanResult"
            ]
        except KeyError as e:
            raise KeyError("No Dpas Result in file, perhaps not a pKa assay?")

    @property
    def mean_pka_values(self) -> float:
        return float(self._mean_dpas_result["MeanPkaResults"]["#text"])

    @property
    def mean_pka_std_values(self) -> float:
        return float(self._mean_dpas_result["MeanPkasStdDevs"]["#text"])

    @property
    def mean_pka_ionic_strengths(self) -> float:
        return float(self._mean_dpas_result["MeanPkasAverageIonicStrength"]["#text"])

    @property
    def mean_pka_temperatures(self) -> float:
        return float(self._mean_dpas_result["MeanPkasAverageTemperature"]["#text"])

    @cached_property
    def predicted_pKa(self) -> PkaResult:
        data = self._doc["DirectControlAssayResultsFile"]["ProcessedData"][
            "PhMetricModel"
        ]["Sample"]["Pka"]
        predicted_type = PkaType(data["PkaType"]["Value"])
        predicted_value = float(data["PkaValue"]["Value"])
        prediction_source = data["PkaValue"]["Source"]
        return PkaResult(
            value=predicted_value,
            std=None,
            pka_type=predicted_type,
            source=prediction_source,
        )


class LogPT3RExtractor(BaseT3RExtractor):
    """
    Class to handle results file from a LogP experiment
    """

    EXPECTED_ASSAY_CATEGORY = AssayCategory.LOGP

    @cached_property
    def logp_result(self) -> LogPResult:
        data = self._doc["DirectControlAssayResultsFile"]["ProcessedData"][
            "MultisweepPhMetricResult"
        ]
        rmsd = float(data["Rmsd"])
        value_list = data["MultisweepPhMetricLevelResult"]["SampleValues"]["Logp"]
        # NEED TO VERIFY THIS WILL BE CORRECT - THIS JUST TAKES THE LARGER OF TWO LOGP VALUES
        value = max(float(value) for value in value_list)
        return LogPResult(value=value, rmsd=rmsd)

    @property
    def logp_solvent(self) -> str:
        return self._doc["DirectControlAssayResultsFile"]["AssayData"]["AssayTemplate"][
            "Settings"
        ]["PartitionType"]["Value"]["#text"]
