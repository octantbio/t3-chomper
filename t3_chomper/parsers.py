from datetime import datetime
from dataclasses import dataclass
import enum
from functools import cached_property
import pathlib
import re
from typing import Optional, Union

import xmltodict

from t3_chomper.logger import get_logger

logger = get_logger(__name__)

## TODO:
## - How to ensure the right logP
## - What other values do we want to extract from result files?


class CaseInsensitiveStrEnum(enum.StrEnum):
    """Enum that lets us refer to elements in a case-insensitive way"""

    @classmethod
    def _missing_(cls, value):
        for member in cls:
            value = str(value).lower()
            if member.value == value:
                return member


class AssayCategory(CaseInsensitiveStrEnum):
    """Assay categories that we consider"""

    PKA = enum.auto()
    LOGP = enum.auto()


class PkaType(CaseInsensitiveStrEnum):
    """Possible pKa types"""

    ACID = enum.auto()
    BASE = enum.auto()

    @property
    def lower(self) -> str:
        """return lowercase name"""
        return self.name.lower()


@dataclass
class PkaResult:
    """Container for a single pKa result or prediction"""

    value: float
    std: Optional[float] = None
    pka_type: Optional[PkaType] = None
    ionic_strength: Optional[float] = None
    temperature: Optional[float] = None
    source: Optional[str] = None


@dataclass
class LogPResult:
    """Container for a single logP result"""

    value: float
    rmsd: float
    solvent: str


def get_assay_category(filename: Union[str, pathlib.Path]) -> AssayCategory:
    """Utility function to quickly get the assay category for a provided t3r file"""

    with open(filename) as fin:
        res = re.findall(r"<Category>(\w+)</Category>", fin.read())
    if len(res) == 1:
        return AssayCategory(res[0])
    else:
        raise ValueError("Could not determine assay category")


class BaseT3RParser:
    """
    Base class for parsing data from T3R files.
    Subclasses can be defined for specific experimental protocols.
    This base class defines properties common to all t3r result files.
    """

    EXPECTED_ASSAY_CATEGORY = None

    def __init__(self, filename: Union[str, pathlib.Path]) -> None:
        self._filename = pathlib.Path(filename)
        self._doc: dict = {}
        self._load_document()

        if self.assay_category != self.EXPECTED_ASSAY_CATEGORY:
            raise ValueError("Input file is not the expected assay type")

    def _load_document(self):
        try:
            with open(self.filename, "rb") as fin:
                self._doc = xmltodict.parse(fin)
                logger.info(f"Loaded file {self.filename}")
        except Exception as e:
            logger.error(f"Error loading file: {self.filename}: {e}")

    @property
    def filename(self) -> pathlib.Path:
        return self._filename

    @property
    def assay_name(self) -> str:
        return self._doc["DirectControlAssayResultsFile"]["Summary"]["AssayName"]

    @property
    def assay_datetime(self) -> datetime:
        str_datetime = self._doc["DirectControlAssayResultsFile"]["Summary"][
            "StartTime"
        ]
        return datetime.fromisoformat(str_datetime)

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


class UVMetricPKaT3RParser(BaseT3RParser):
    """
    Class to handle results file from pKa Experiment
    """

    EXPECTED_ASSAY_CATEGORY = AssayCategory.PKA

    @property
    def result_list(self) -> list[dict]:
        """
        Return result summary as a list of dict objects, one for each pKa
        """
        results = []
        for pka_number, pka in enumerate(self.pka_results, start=1):
            results.append(
                {
                    "sample": self.sample_name,
                    "filename": self.filename.name,
                    "assay_name": self.assay_name,
                    "assay_quality": self.assay_quality,
                    "pka_number": pka_number,
                    "pka_type": pka.pka_type,
                    "pka_value": pka.value,
                    "pka_std": pka.std,
                    "pka_ionic_strength": pka.ionic_strength,
                    "pka_temperature": pka.temperature,
                    "cosolvent": self.cosolvent_name,
                    "cosolvent_fractions": self.cosolvent_fractions,
                }
            )
        return results

    @property
    def result_dict(self) -> dict:
        """
        Return a result summary as a single dict
        """
        return {
            "filename": self.filename.name,
            "sample": self.sample_name,
            "assay_name": self.assay_name,
            "assay_quality": self.assay_quality,
            "pka_list": [result.value for result in self.pka_results],
            "std_list": [result.std for result in self.pka_results],
            "ionic_strength_list": [
                result.ionic_strength for result in self.pka_results
            ],
            "temp_list": [result.temperature for result in self.pka_results],
            "cosolvent": self.cosolvent_name,
            "cosolvent_fractions": self.cosolvent_fractions,
            "reformatted_pkas": self.t3_formatted_results,
        }

    @property
    def _fastdpas_mean_results(self) -> list[PkaResult]:
        """
        pKa result(s) from the "FastDpasMeanResult" element
        Assumes that multiple pKas are found as space-separated values under the element named:
        "ProcessedData.FastDPasMeanResult.MeanPkaResults"
        """
        obj = self._doc["DirectControlAssayResultsFile"]["ProcessedData"][
            "FastDpasMeanResult"
        ]
        num_pkas = int(obj["MeanPkaResults"]["@size"])
        results = []
        for pka in range(num_pkas):
            results.append(
                PkaResult(
                    value=float(obj["MeanPkaResults"]["#text"].split(" ")[pka]),
                    std=float(obj["MeanPkasStdDevs"]["#text"].split(" ")[pka]),
                    ionic_strength=float(
                        obj["MeanPkasAverageIonicStrength"]["#text"].split(" ")[pka]
                    ),
                    temperature=float(
                        obj["MeanPkasAverageTemperature"]["#text"].split(" ")[pka]
                    ),
                )
            )
        return results

    @property
    def _dielectric_fit_result(self) -> list[PkaResult]:
        """
        Get pKa results from the YasudaShedlovskyResult.DielectircFit element
        Assumes that pKa values are found as elements under
        "ProcessedData.YasudaShedlovskyResult.DielectricFit"
        """
        obj = self._doc["DirectControlAssayResultsFile"]["ProcessedData"][
            "YasudaShedlovskyResult"
        ]["DielectricFit"]["YasudaShedlovskyFit"]

        # Force to a list
        if not isinstance(obj, list):
            obj = [obj]

        results = [
            PkaResult(
                value=float(fit["AqueousPka"]),
                std=float(fit["ConfidenceInterval"]),
                ionic_strength=float(fit["AverageIonicStrength"]),
                temperature=float(fit["AverageTemperature"]),
            )
            for fit in obj
        ]
        return results

    @property
    def pka_results(self) -> list[PkaResult]:
        """
        Get measured pKa results.
        Look under the "FastDPasMeanResult" tree for results first, then if not found,
        look under "ProcessedData.YasudaShedlovskyResult.DielectricFit"
        """
        try:
            results = self._fastdpas_mean_results
        except KeyError:
            try:
                results = self._dielectric_fit_result
            except KeyError:
                raise KeyError(f"Could not find pKa results in file: {self.filename}")
        for measured, predicted in zip(results, self.predicted_pka):
            measured.pka_type = predicted.pka_type

        return results

    @property
    def predicted_pka(self) -> list[PkaResult]:
        """Get the predicted pKa values input into the experiment"""
        obj = self._doc["DirectControlAssayResultsFile"]["ProcessedData"][
            "PhMetricModel"
        ]["Sample"]["Pka"]

        if not isinstance(obj, list):
            obj = [obj]

        return [
            PkaResult(
                value=float(pred["PkaValue"]["Value"]),
                std=None,
                pka_type=PkaType(pred["PkaType"]["Value"]),
                source=pred["PkaValue"]["Source"],
            )
            for pred in obj
        ]

    @property
    def t3_formatted_results(self) -> str:
        """
        SririusT3-formatted pKa results
        The format should be comma-separated values of <type>,<value>, e.g.,
        "acid,2.86,base,9.64"
        This assumes that the measured results are in the same order as the predicted pKas
        """
        predicted_pkas = self.predicted_pka
        measured_pkas = self.pka_results
        return ",".join(
            f"{pred.pka_type.lower},{meas.value}"
            for pred, meas in zip(predicted_pkas, measured_pkas)
        )

    @property
    def cosolvent_name(self) -> str | None:
        """
        Get Name of cosolvent used
        """
        base = self._doc["DirectControlAssayResultsFile"]["ProcessedData"]
        if "Sweep" not in base:
            return None
        try:
            first_sweep = base["Sweep"][0]
            solvent_name = first_sweep["FastDpasResult"]["CosolventRatio"][
                "CosolventName"
            ]
            return solvent_name
        except (KeyError, IndexError):
            logger.error(f"Could not extract cosolvent name from {self.filename}")

    @property
    def cosolvent_fractions(self) -> list[float] | None:
        """
        Get a list of the cosolvent fractions by weight
        """
        try:
            sweeps = self._doc["DirectControlAssayResultsFile"]["ProcessedData"][
                "Sweep"
            ]
            fractions = [
                float(sweep["FastDpasResult"]["CosolventRatio"]["WtFraction"])
                for sweep in sweeps
            ]
            return fractions
        except (KeyError, IndexError):
            logger.error(f"Could not extract cosolvent fractions from {self.filename}")


class LogPT3RParser(BaseT3RParser):
    """
    Class to handle results file from a LogP experiment
    """

    EXPECTED_ASSAY_CATEGORY = AssayCategory.LOGP

    @property
    def result_dict(self) -> dict:
        """Return parsed results as a dict"""
        return {
            "filename": self.filename.name,
            "sample": self.sample_name,
            "assay_name": self.assay_name,
            "assay_quality": self.assay_quality,
            "logp": self.logp_result.value,
            "rmsd": self.logp_result.rmsd,
            "solvent": self.logp_result.solvent,
        }

    @cached_property
    def logp_result(self) -> LogPResult:
        data = self._doc["DirectControlAssayResultsFile"]["ProcessedData"][
            "MultisweepPhMetricResult"
        ]
        rmsd = float(data["Rmsd"])
        value_list = data["MultisweepPhMetricLevelResult"]["SampleValues"]["Logp"]
        # NEED TO VERIFY THIS WILL BE CORRECT - THIS JUST TAKES THE LARGER OF TWO LOGP VALUES
        value = max(float(value) for value in value_list)
        solvent = self.logp_solvent
        return LogPResult(value=value, rmsd=rmsd, solvent=solvent)

    @property
    def logp_solvent(self) -> str:
        return self._doc["DirectControlAssayResultsFile"]["AssayData"]["AssayTemplate"][
            "Settings"
        ]["PartitionType"]["Value"]["#text"]
