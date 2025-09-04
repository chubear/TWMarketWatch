"""
TDCC (Taiwan Depository & Clearing Corporation) Data Crawler
============================================================

This module provides functionality to crawl stockholder structure data from
Taiwan Depository & Clearing Corporation OpenAPI.
"""

from .tdcc_stockholder_structure import TDCCStockholderStructure

__version__ = "1.0.0"
__all__ = ['TDCCStockholderStructure']