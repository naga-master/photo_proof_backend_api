"""Compatibility wrapper for the DataManager service."""

from app.services.data_manager import DataManager

data_manager = DataManager()

__all__ = ["DataManager", "data_manager"]
