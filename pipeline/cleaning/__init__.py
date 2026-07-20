"""Cleaning pipeline: timeseries, VSIC validation, marketplace, orchestrator."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pipeline.cleaning.run_cleaning import run_data_cleaning as run_data_cleaning

__all__ = ["run_data_cleaning"]


def __getattr__(name: str):
    if name == "run_data_cleaning":
        from pipeline.cleaning.run_cleaning import run_data_cleaning

        return run_data_cleaning
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
