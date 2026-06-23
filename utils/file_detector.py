"""
Utility: Auto-detects file format and routes to the correct extractor.
Supports: PDF, JPG, PNG, CSV, Excel, JSON
"""

import os

SUPPORTED_FORMATS = {
    "pdf":   [".pdf"],
    "image": [".jpg", ".jpeg", ".png", ".bmp", ".tiff"],
    "csv":   [".csv"],
    "excel": [".xlsx", ".xls"],
    "json":  [".json"],
}

def detect_format(file_path: str) -> str:
    ext = os.path.splitext(file_path)[-1].lower()
    for fmt, extensions in SUPPORTED_FORMATS.items():
        if ext in extensions:
            return fmt
    return "unknown"

def is_supported(file_path: str) -> bool:
    return detect_format(file_path) != "unknown"