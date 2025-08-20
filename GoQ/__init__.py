"""
GoQ Package - Web automation for GoQ system
"""

from .GoQ import GoQ

# Package metadata
__version__ = "1.0.0"
__author__ = "AI Agents Project"
__description__ = "Web automation package for GoQ order management system"

# Package-level constants
DEFAULT_TIMEOUT = 10000
DEFAULT_ERROR_FILE_PREFIX = "error_"
DEFAULT_TABLE_DATA_FILE = "table_data.json"

# Export control - what gets imported with "from GoQ import *"
__all__ = [
    'GoQ',
    'DEFAULT_TIMEOUT', 
    'DEFAULT_ERROR_FILE_PREFIX',
    'DEFAULT_TABLE_DATA_FILE'
]