# Snap7

This is a fork of http://snap7.sourceforge.net/


This fork focuses on extending the Snap7Server module to support some features helping to implement a software PLC.
These features are currently:
* support for program blocks (up-/download, listing)
* some dynamic SZLs
* vartable watching
* monitor mode

For more details I refer to the commit history.
Please note that this fork is currently at version 1.4.0.

Cleanup, more fixes and documentation will follow.

## License

This repository includes the applicable license texts in the repository root:

- [GPL license text](gpl.txt)
- [LGPL v3.0 license text](lgpl-3.0.txt)

Please review the applicable license terms before using, modifying,
or redistributing this software.

## Fork Status

This repository is a community-maintained fork of
[SCADACS/snap7](https://github.com/SCADACS/snap7).

The original Snap7 project and its contributors retain credit for the
upstream codebase. This fork adds independently maintained documentation,
build, testing, security, and integration improvements.

See the repository history and license texts for applicable notices.

## Security

For security considerations when deploying Snap7 in industrial environments,
see [SECURITY.md](SECURITY.md), [docs/secure-deployment.md](docs/secure-deployment.md),
and [docs/industrial-networking.md](docs/industrial-networking.md).

## Continuous Integration

This project includes GitHub Actions workflows for cross-platform builds
and automated smoke tests on Linux and Windows.
