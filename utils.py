"""
Shared utilities for AI Agents project
"""

import os
import json
import time
from datetime import datetime


def ensure_directory(path):
    """Create directory if it doesn't exist"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"[Error] Failed to create directory {path}: {e}")
        return False


def save_json(data, filename, encoding="utf-8", indent=2):
    """Save data to JSON file with error handling"""
    try:
        with open(filename, "w", encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        print(f"[Error] Failed to save JSON to {filename}: {e}")
        return False


def load_json(filename, encoding="utf-8"):
    """Load data from JSON file with error handling"""
    try:
        if not os.path.exists(filename):
            return {}
        with open(filename, "r", encoding=encoding) as f:
            return json.load(f)
    except Exception as e:
        print(f"[Error] Failed to load JSON from {filename}: {e}")
        return {}


def generate_timestamp_filename(prefix="", suffix="", extension="json"):
    """Generate filename with timestamp"""
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}{now}{suffix}.{extension}"


def save_html_debug(content, filename, folder="html_output"):
    """Save HTML content for debugging"""
    try:
        ensure_directory(folder)
        filepath = os.path.join(folder, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[Debug] HTML saved to {filepath}")
        return True
    except Exception as e:
        print(f"[Error] Failed to save HTML to {filename}: {e}")
        return False


def log_error_with_timestamp(message, level="ERROR"):
    """Log message with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


# Package metadata
__version__ = "1.0.0"
__author__ = "AI Agents Project"