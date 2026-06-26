"""Data loading utilities for the GitHub Repository Health Analyzer."""
from pathlib import Path
import pandas as pd


def load_commits_csv(path: str) -> pd.DataFrame:
    """Load commits CSV into a DataFrame."""
    p = Path(path)
    return pd.read_csv(p)
