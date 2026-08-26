/**
 * Snap7 Node.js Wrapper (Work In Progress)
 *
 * Design principles:
 * - Read-only by default.
 * - Configuration via environment variables only.
 * - No hardcoded PLC addresses.
 */

'use strict';

const config = {
  host: process.env.SNAP7_HOST || '127.0.0.1',
  rack: parseInt(process.env.SNAP7_RACK || '0', 10),
  slot: parseInt(process.env.SNAP7_SLOT || '1', 10),
  enableWrites: (process.env.SNAP7_ENABLE_WRITES || 'false') === 'true',
};

function createReader() {
  return {
    config,
    connect() {
      throw new Error(
        'This wrapper is a work in progress. ' +
        'Connection logic will bind to the native Snap7 library.'
      );
    },
    readDataBlock(_dbNumber, _start, _size) {
      throw new Error(
        'Read logic will be implemented after native binding is ready.'
      );
    },
  };
}

module.exports = { config, createReader };