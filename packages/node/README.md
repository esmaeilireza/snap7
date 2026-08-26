# Snap7 Node.js Wrapper

A modern TypeScript-friendly wrapper around the Snap7 native library.

## Status

This is a work in progress. It will expose typed APIs for reading
PLC telemetry through the native Snap7 library.

## Design Rules

- Read-only by default.
- Typed interfaces for TypeScript users.
- Configuration via environment variables.
- Local mock / simulator path for testing.