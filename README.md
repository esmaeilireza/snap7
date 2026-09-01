# Snap7 – Industrial Communication Toolkit

[![License: LGPL v3](https://img.shields.io/badge/License-LGPLv3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![CI](https://github.com/SCADACS/snap7/actions/workflows/smoke-test.yml/badge.svg)](https://github.com/SCADACS/snap7/actions)

Snap7 is an open-source, multi-platform Ethernet suite that natively connects to Siemens S7 PLCs. This repository is a **community-maintained fork** of the original [Snap7](http://snap7.sourceforge.net/) project, designed to bridge the gap between industrial automation and modern software engineering practices.

It extends the core library with features tailored for building **software PLCs, modern SCADA interfaces, and data-driven industrial applications**.

---

## 🎯 Key Features & Enhancements

Industrial automation code often lacks modern software practices such as version control, automated testing, and security audits. This fork addresses those gaps by introducing:

- **Program Block Management**: Programmatically upload, download, and list PLC blocks.
- **Dynamic SZL Support**: Query system status lists (SZL) for advanced diagnostics.
- **Variable Watching & Monitor Mode**: Enable real-time debugging and monitoring.
- **Modern Python/Tkinter Dashboard**: A fully functional, live SCADA-like UI featuring real-time charts, asset tables, and alarm management.

---

## 🚀 Quick Start: Live Dashboard Demo

This repository includes a Python-based SCADA dashboard that connects to any Snap7 server, whether it's a real PLC or a software simulation.

### Running in Simulation Mode

1. Navigate to the demo directory:
   ```bash
   cd demo
   ```
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the dashboard in simulation mode:
   ```bash
   python scada_dashboard.py --simulate
   ```

**Dashboard Capabilities:**
- Real-time temperature and data charting.
- Asset table for monitoring connected PLCs and sensors.
- Comprehensive communication logging.
- Alarm management and system trend reporting.

> *Note: Ensure you have a working display environment to view the Tkinter GUI.*

---

## 📁 Project Structure

The repository is organized to keep the core C++ library separate from the modern Python tooling and documentation.

```text
snap7/
├── demo/                     # Python SCADA dashboard and simulation tools
│   ├── scada_dashboard.py    # Main entry point for the GUI
│   ├── fork_bridge.py        # Snap7 client/server bridge implementation
│   ├── sensor_simulator.py   # Simulated PLC data generator
│   ├── test_bridge.py        # Unit tests for the bridge
│   ├── apply_patch_fork.py   # Utility to apply custom patches
│   ├── run_dashboard.bat     # Windows execution launcher
│   ├── requirements.txt      # Python dependencies
│   └── ui/                   # Tkinter User Interface components
│       ├── asset_panel.py    # Connected assets list
│       ├── chart_widget.py   # Live data chart
│       ├── dashboard_ui.py   # Main dashboard layout
│       ├── log_widget.py     # Communication log viewer
│       ├── status_cards.py   # System status & connection cards
│       ├── theme.py          # Dark industrial color theme
│       ├── views.py          # View manager and logic
│       └── widgets.py        # Reusable UI widgets (LEDs, badges, etc.)
├── src/                      # Core Snap7 C++ source code
│   ├── core/                 # S7 protocol implementation
│   ├── lib/                  # Library entry points (snap7.def, libmain)
│   └── sys/                  # Platform abstraction layer (threads, sockets)
├── docs/                     # Extended documentation
│   ├── secure-deployment.md  # Guidelines for secure industrial deployment
│   └── industrial-networking.md
├── tools/                    # Auxiliary scripts and utilities
├── README.md                 # Project overview (this file)
├── SECURITY.md               # Security policies and reporting
├── gpl.txt                   # GPL license text
├── lgpl-3.0.txt              # LGPLv3 license text
└── HISTORY.txt               # Version history and changelog
```

---

## 📦 Installation (Pre-built Binaries)

For immediate use, download the latest release package from the [Releases Page](https://github.com/SCADACS/snap7/releases). The archives are portable and require no system-wide installation.

**Platform-Specific Library Locations:**

| Platform       | Architecture | Library Path                          |
|----------------|--------------|---------------------------------------|
| **Windows**    | 32-bit       | `release/Windows/Win32/snap7.dll`     |
| **Windows**    | 64-bit       | `release/Windows/Win64/snap7.dll`     |
| **Linux**      | x86_64       | `release/Linux/x86_64/libsnap7.so`    |
| **Linux (ARM)**| ARMv7 (RPi)  | `release/Linux/arm_v7/libsnap7.so`    |

Simply copy the appropriate library file to your system library path or directly into your application's working directory.

---

## 🔧 Building from Source

### Prerequisites

- **Linux (Ubuntu/Debian):** 
  ```bash
  sudo apt-get update && sudo apt-get install build-essential
  ```
- **Windows (MSYS2):** 
  Install [MSYS2](https://www.msys2.org/), then install the MinGW-w64 toolchain:
  ```bash
  pacman -S --needed mingw-w64-x86_64-gcc mingw-w64-x86_64-binutils make
  ```

### Compiling the Core Library

- **Linux (x86_64):**
  ```bash
  cd build/unix
  make -f x86_64_linux.mk
  ```

- **Windows (MinGW64):**
  ```bash
  cd build/windows/MinGW64
  make
  ```

### Building and Running Tests

To verify your build, compile and run the loopback test:
```bash
cd examples/cpp/<your-platform>
make
./loopback_test
```

---

## 🔌 Python Wrapper Usage

The most straightforward way to interact with Snap7 via Python is by utilizing the included dashboard code as a reference. 

**Basic Client Example:**
```python
from demo.fork_bridge import ForkClient

# Initialize and connect to the PLC
client = ForkClient()
client.connect("192.168.1.1", 0, 1)

# Read 100 bytes from DB1 starting at offset 0
data = client.db_read(1, 0, 100)
print(data)

# Cleanly disconnect
client.disconnect()
```

---

## 🔄 Continuous Integration

This project leverages GitHub Actions to ensure code quality and stability across platforms:

- **Smoke Tests**: Automated building and execution of loopback tests on Ubuntu and Windows.
- **CodeQL Analysis**: Continuous security and code quality scanning for C/C++.
- **Issue Management**: Automated triage and stale issue bot to keep the tracker organized.

---

## 🔐 Security

Deploying software in industrial environments requires strict adherence to security best practices. Before deploying, please review our security documentation:

- [SECURITY.md](SECURITY.md) - Vulnerability reporting and security policies.
- [docs/secure-deployment.md](docs/secure-deployment.md) - Hardening guidelines.
- [docs/industrial-networking.md](docs/industrial-networking.md) - Network isolation and safety.

---

## 📄 License

This project is licensed under the **GNU Lesser General Public License v3.0 (LGPLv3)**. 
Please refer to the [LGPL-3.0](lgpl-3.0.txt) and [GPL](gpl.txt) files for the full legal text.

---

## 🙌 Contributing

Contributions are highly encouraged! Whether it's fixing bugs, adding new features, or improving documentation, please feel free to open an issue or submit a pull request.

---

## 🌐 Acknowledgments

- **Davide Nardella** and the original Snap7 authors for creating an outstanding and robust foundational library.
- The **Industrial Automation Community** for continuous feedback, real-world testing, and inspiration.
```