"""Logging layer for events and errors."""

from datetime import datetime


def log_event(stage: str, data: str) -> None:
    """
    Log an event at a specific stage.
    
    Args:
        stage: The pipeline stage name
        data: The data to log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[LOG] [{timestamp}] [{stage}] {data}")


def log_error(stage: str, error: str) -> None:
    """
    Log an error at a specific stage.
    
    Args:
        stage: The pipeline stage name
        error: The error message to log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[ERROR] [{timestamp}] [{stage}] {error}")

