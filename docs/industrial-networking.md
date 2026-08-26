# Industrial Networking Guidance

This document provides guidance on network architecture and communication patterns when using Snap7 in industrial environments.

## Network Segmentation

Industrial control systems should be separated from enterprise IT networks using:

- **DMZ / Industrial DMZ**: A controlled boundary between IT and OT networks
- **Firewalls**: Stateful inspection firewalls with rules allowing only necessary protocols and ports
- **VLANs**: Logical separation of traffic types (e.g., HMI, historian, engineering, safety)
- **Unidirectional Gateways (Data Diodes)**: For high-security environments requiring data flow from OT to IT only

## Communication Protocols

Snap7 uses the Siemens S7 protocol over ISO-on-TCP (RFC 1006) typically on port 102. Consider:

- Restricting port 102 access to authorized engineering stations only
- Using non-standard ports where possible to reduce automated scanning
- Implementing port knocking or SPA (Single Packet Authorization) for additional obscurity

## Redundancy and Availability

- Design network paths with redundancy for critical communication
- Implement monitoring for communication loss and latency anomalies
- Consider PLC-side communication load when multiple clients connect
- Use Snap7's connection management features to handle reconnections gracefully

## Monitoring and Logging

- Log all connection attempts (successful and failed)
- Monitor for unusual traffic patterns or unexpected PLC commands
- Correlate network logs with PLC diagnostic buffers
- Set up alerts for communication failures on critical assets

## Remote Access

If remote access is required:

- Use a dedicated VPN with multi-factor authentication
- Implement jump hosts / bastion hosts for engineering access
- Record and audit all remote sessions
- Enforce time-limited access with automatic revocation

## References

- IEC 62443 Series - Industrial communication network security
- NIST SP 800-82 - Guide to Industrial Control Systems Security
- ISA/IEC 62443-3-3 - System security requirements and security levels