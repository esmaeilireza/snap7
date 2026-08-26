# Secure Deployment Guide

This guide provides security-focused deployment recommendations for systems using Snap7 to communicate with Siemens S7 PLCs.

## Network Architecture

- PLCs should not be exposed directly to the internet.
- Use network segmentation and firewall rules to isolate OT networks from IT networks.
- Use VPN or controlled remote-access mechanisms for remote engineering access.
- Limit access to authorized engineering and service networks only.
- Use least-privilege access where supported by the PLC and network infrastructure.

## Operational Security

- Treat PLC write operations as high-risk actions.
- Separate development/test devices from production assets.
- Log, monitor, and review communication failures and unexpected commands.
- Implement change management procedures for any modifications to PLC programs or configuration.

## Important Limitations

Snap7 is not a substitute for OT network architecture and operational security controls. It provides communication capabilities but does not implement:

- Network-level authentication or encryption (relies on underlying transport)
- Industrial firewall or intrusion detection
- Safety system functions
- Compliance with specific industrial security standards (e.g., IEC 62443)

These controls must be implemented at the network and system architecture level.