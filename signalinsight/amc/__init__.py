"""Automatic Modulation Classification (AMC) subsystem."""

from signalinsight.amc.base import BaseModulationClassifier
from signalinsight.amc.classifier import XGBoostModulationClassifier
from signalinsight.amc.synthetic import SyntheticSignalGenerator

__all__ = [
    "BaseModulationClassifier",
    "XGBoostModulationClassifier",
    "SyntheticSignalGenerator",
]
