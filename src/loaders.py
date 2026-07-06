"""
loaders.py
----------
Utility functions for loading raw AENA / ENAIRE datasets into pandas DataFrames.

Usage example
-------------
>>> from src.loaders import load_aena_passengers
>>> df = load_aena_passengers()
>>> df.head()
"""

from __future__ import annotations

import glob
import os
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Default paths (can be overridden via environment variables)
# ---------------------------------------------------------------------------
_BASE = Path(__file__).parent.parent  # repository root
_RAW = Path(os.getenv("DATA_RAW_DIR", _BASE / "data" / "raw"))
_PROCESSED = Path(os.getenv("DATA_PROCESSED_DIR", _BASE / "data" / "processed"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_csv_glob(pattern: str, **kwargs) -> pd.DataFrame:
    """Read all CSV files matching *pattern* and concatenate them."""
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files found matching: {pattern}")
    return pd.concat([pd.read_csv(f, **kwargs) for f in files], ignore_index=True)


# ---------------------------------------------------------------------------
# AENA – Passengers
# ---------------------------------------------------------------------------

def load_aena_passengers(**kwargs) -> pd.DataFrame:
    """
    Load AENA monthly passenger statistics.

    Returns
    -------
    pd.DataFrame
        Raw passengers DataFrame with all available columns.
    """
    pattern = str(_RAW / "aena_passengers" / "*.csv")
    return _read_csv_glob(pattern, **kwargs)


# ---------------------------------------------------------------------------
# AENA – Airlines
# ---------------------------------------------------------------------------

def load_aena_airlines(**kwargs) -> pd.DataFrame:
    """
    Load AENA airline directory data.

    Returns
    -------
    pd.DataFrame
    """
    pattern = str(_RAW / "aena_airlines" / "*.csv")
    return _read_csv_glob(pattern, **kwargs)


# ---------------------------------------------------------------------------
# AENA – Airports
# ---------------------------------------------------------------------------

def load_aena_airports(**kwargs) -> pd.DataFrame:
    """
    Load AENA airport metadata.

    Returns
    -------
    pd.DataFrame
    """
    pattern = str(_RAW / "aena_airports" / "*.csv")
    return _read_csv_glob(pattern, **kwargs)


# ---------------------------------------------------------------------------
# ENAIRE – AIP documents
# ---------------------------------------------------------------------------

def load_enaire_aip_texts(extension: str = "*.txt") -> list[dict]:
    """
    Load ENAIRE AIP raw text files.

    Parameters
    ----------
    extension : str
        Glob pattern for the file extension (default ``*.txt``).

    Returns
    -------
    list[dict]
        List of ``{"source": <path>, "content": <text>}`` dicts.
    """
    pattern = str(_RAW / "enaire_aip" / extension)
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files found matching: {pattern}")
    docs = []
    for path in files:
        with open(path, encoding="utf-8") as fh:
            docs.append({"source": path, "content": fh.read()})
    return docs


# ---------------------------------------------------------------------------
# Processed data
# ---------------------------------------------------------------------------

def save_processed(df: pd.DataFrame, name: str, **kwargs) -> Path:
    """
    Save a DataFrame to the processed data directory as a CSV.

    Parameters
    ----------
    df : pd.DataFrame
    name : str
        File name without extension.

    Returns
    -------
    Path
        Path to the saved file.
    """
    _PROCESSED.mkdir(parents=True, exist_ok=True)
    out = _PROCESSED / f"{name}.csv"
    df.to_csv(out, index=False, **kwargs)
    return out


def load_processed(name: str, **kwargs) -> pd.DataFrame:
    """
    Load a processed CSV by name.

    Parameters
    ----------
    name : str
        File name without extension.

    Returns
    -------
    pd.DataFrame
    """
    path = _PROCESSED / f"{name}.csv"
    return pd.read_csv(path, **kwargs)
