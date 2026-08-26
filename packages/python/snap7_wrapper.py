"""
Snap7 Python Wrapper (Work In Progress)

This is a safe, read-only oriented wrapper design for the Snap7 library.
It is intended to be used for telemetry and monitoring use cases.

Design principles:
- Read-only by default.
- Configuration via environment variables only.
- No hardcoded PLC addresses.
"""

import os


class Snap7Config:
    """Configuration loaded strictly from environment variables."""

    def __init__(self):
        self.host = os.getenv("SNAP7_HOST", "127.0.0.1")
        self.rack = int(os.getenv("SNAP7_RACK", "0"))
        self.slot = int(os.getenv("SNAP7_SLOT", "1"))
        self.enable_writes = os.getenv("SNAP7_ENABLE_WRITES", "false").lower() == "true"


class Snap7Reader:
    """
    A placeholder for a read-only Snap7 client wrapper.

    The real implementation will load the native Snap7 library
    and expose safe read methods for telemetry use cases.
    """

    def __init__(self, config: Snap7Config):
        self.config = config

    def connect(self):
        raise NotImplementedError(
            "This wrapper is a work in progress. "
            "Connection logic will bind to the native Snap7 library."
        )

    def read_data_block(self, db_number: int, start: int, size: int):
        raise NotImplementedError(
            "Read logic will be implemented after native binding is ready."
        )