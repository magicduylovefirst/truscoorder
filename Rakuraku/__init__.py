"""
Rakuraku Package - Web automation for Rakuraku system
"""

from .Rakuraku import Rakuraku

# Package metadata
__version__ = "1.0.0"
__author__ = "AI Agents Project"
__description__ = "Web automation package for Rakuraku order management system"

# Package-level constants
DEFAULT_TIMEOUT = 10000
DEFAULT_TABLE_DATA_FILE = "table_data.json"
DEFAULT_DOWNLOAD_DIR = "Downloads"

# UI element selectors
CREATE_MITSUKOMI_SELECTOR = '#actionButton_106853'
CREATE_ORDER_SELECTOR = '#actionButton_106851'

# Status constants
BREAK_POINT_STATUS = '発注済'

# Valuable header indices for data extraction
VALUABLE_INDICES = [1, 6, 7, 8, 11, 12, 13]

# Export control - what gets imported with "from Rakuraku import *"
__all__ = [
    'Rakuraku',
    'DEFAULT_TIMEOUT',
    'DEFAULT_TABLE_DATA_FILE',
    'DEFAULT_DOWNLOAD_DIR',
    'CREATE_MITSUKOMI_SELECTOR',
    'CREATE_ORDER_SELECTOR',
    'BREAK_POINT_STATUS',
    'VALUABLE_INDICES'
]