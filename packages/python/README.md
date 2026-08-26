# Snap7 Python Wrapper

A modern, Pythonic wrapper around the Snap7 native library.

## Status

This is a work in progress. It provides a read-only telemetry interface
on top of the Snap7 core.

## Design Rules

- Read-only by default.
- No hardcoded PLC IP addresses.
- Configuration through environment variables.
- Uses the native Snap7 library loaded from the local platform.