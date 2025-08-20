"""
Orange Package - Web automation for Orange-Book system
"""

from .Orange import Orange

# Package metadata
__version__ = "1.0.0"
__author__ = "AI Agents Project"
__description__ = "Web automation package for Orange-Book order processing system"

# Package-level constants
DEFAULT_TIMEOUT = 10000
DEFAULT_ERROR_FILE = "error.json"
DEFAULT_TABLE_DATA_FILE = "table_data.json"
MTR_LINK = "https://www.orange-book.com/ja/f/view/OB3110S23001.xhtml?definiteFileType=2"
TRI_LINK = "https://www.orange-book.com/ja/f/view/OB3110S23001.xhtml?definiteFileType=1"

# Common warning messages
WARNING_MESSAGES = [
    "本商品は、廃番商品のため、注文できません。"
]

# Export control - what gets imported with "from Orange import *"
__all__ = [
    'Orange',
    'DEFAULT_TIMEOUT',
    'DEFAULT_ERROR_FILE', 
    'DEFAULT_TABLE_DATA_FILE',
    'MTR_LINK',
    'TRI_LINK',
    'WARNING_MESSAGES'
]