# Snap7 – Industrial Ethernet Communication Suite (Extended Fork)

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](LICENSE)
[![CI](https://github.com/esmaeilireza/snap7/actions/workflows/build.yml/badge.svg)](https://github.com/esmaeilireza/snap7/actions)
[![C++](https://img.shields.io/badge/Language-C%2B%2B%20%7C%20C%20%7C%20Python-orange.svg)]()

**Snap7** is an open-source, 32/64-bit multi-platform Ethernet communication suite designed for native interfacing with Siemens S7 PLCs (S7-200, S7-300, S7-400, S7-1200, and S7-1500).

This repository is an **extended, community-maintained fork** of the original Snap7 project by Davide Nardella. It maintains full compatibility with the core C/C++ engine while introducing modern build toolchain fixes, continuous integration, typed Python wrappers, and a desktop diagnostic HMI workbench for rapid field commissioning.

---

## 🎯 Fork Enhancements & Additions

While preserving the zero-dependency, high-performance C/C++ core, this fork adds:

* **Toolchain & Build Modernization:** Cleaned MinGW-w64 Makefiles, resolved hardcoded linking paths, and fixed 64-bit integer type issues on modern Windows toolchains.
* **Continuous Integration & Security:** GitHub Actions workflows for automated loopback smoke tests and CodeQL static security analysis.
* **Extended Python Bridge (`demo/fork_bridge.py`):** High-level client wrapper providing typed reads/writes (`REAL`, `INT`, `DINT`, `BOOL`), dynamic SZL parsing, and automated connection management.
* **Dynamic S7 Mock Server (`demo/snap7_server.py`):** Multi-threaded local S7 server with auto-updating Data Blocks (DB1) for offline testing without physical PLC hardware.
* **Modern Diagnostic Station (`demo/`):** PySide6 (Qt) commissioning HMI featuring real-time hardware-accelerated telemetry, connection failover, and protocol event logging.

---

## 🖥️ Diagnostic HMI & Commissioning Workbench

Located in the `demo/` directory, this tool allows automation engineers and developers to test, monitor, and validate S7 communication without installing Step 7 or TIA Portal.

![Diagnostic Workbench Preview](demo/screenshot.png)

### Key Capabilities

| Capability | Description |
| :--- | :--- |
| **Telemetry Dashboard** | Real-time polling and visualization of process metrics and system status |
| **High-Rate Plotting** | Low-overhead, hardware-accelerated time-series graphing powered by `pyqtgraph` |
| **Dynamic Failover** | Automatic fallback to the built-in simulator upon communication timeout |
| **Protocol Event Logging** | Structured, timestamped communication terminal with status codes |
| **Runtime Configuration** | Persistent settings (`config.ini`) for Target IP, Rack, Slot, Port, and Polling Rates |

### Quick Start (Demo Workbench)

```bash
cd demo
pip install -r requirements.txt

```

* **Run in Simulation Mode (No hardware required):**
```bash
python scada_dashboard.py --simulate

```


* **Run with the Dynamic Mock Server:**
```bash
# Terminal 1: Start local S7 server
python snap7_server.py

# Terminal 2: Launch diagnostic client
python scada_dashboard.py

```



---

## 🔌 Python Client Quick Example

The Python bridge (`demo/fork_bridge.py`) wraps the native library for rapid scripting:

```python
from demo.fork_bridge import ForkClient

client = ForkClient()
client.connect("192.168.0.1", rack=0, slot=1)

# Read 100 bytes from DB1 starting at offset 0
raw_bytes = client.db_read(db_number=1, start=0, size=100)

# Typed read (e.g., REAL at offset 4)
temp_value = client.read_real(db_number=1, offset=4)
print(f"Temperature: {temp_value:.2f} °C")

client.disconnect()

```

---

## 📦 Pre-built Binaries

Pre-compiled native binaries are located in the repository:

| Platform | Architecture | Library Path |
| --- | --- | --- |
| **Windows** | 32-bit (x86) | `release/Windows/Win32/snap7.dll` |
| **Windows** | 64-bit (x64) | `release/Windows/Win64/snap7.dll` |
| **Linux** | 64-bit (x86_64) | `release/Linux/x86_64/libsnap7.so` |
| **Linux** | ARMv7 (RPi / Embedded) | `release/Linux/arm_v7/libsnap7.so` |

---

## 🔧 Building the Core C/C++ Library from Source

### Prerequisites

* **Linux (Debian/Ubuntu):**
```bash
sudo apt-get update && sudo apt-get install build-essential

```


* **Windows:** MSYS2 with `mingw-w64-x86_64-gcc` and `make`.

### Compilation

* **Linux (x86_64):**
```bash
cd build/unix
make -f x86_64_linux.mk

```


* **Windows (MinGW-w64):**
```bash
cd build/windows/MinGW64
make

```



### Running Loopback Verification

```bash
cd examples/cpp/<platform>
make
./loopback_test

```

---

## 📁 Repository Layout

```
snap7/
├── demo/                   # Extended tooling, Python bridge, and Qt diagnostic HMI
│   ├── scada_dashboard.py  # Diagnostic station main executable
│   ├── fork_bridge.py      # High-level typed Snap7 Python wrapper
│   ├── snap7_server.py     # Standalone dynamic mock server
│   ├── sensor_simulator.py # Process metric generator
│   └── ui/                 # PySide6 layout components and design tokens
├── src/                    # Core Snap7 C/C++ source code
│   ├── core/               # ISO-on-TCP and S7 protocol stack
│   ├── lib/                # API exports (snap7.def, libmain)
│   └── sys/                # OS abstraction layer (sockets, threads)
├── build/                  # Makefiles for Linux, Windows, macOS, BSD, and Solaris
├── examples/               # Native examples (C/C++, C#, Pascal, LabVIEW)
├── docs/                   # Deployment guides and network architecture notes
├── SECURITY.md             # Security policy and vulnerability disclosure
└── LICENSE                 # LGPL-3.0 License

```

---

## 🔐 Industrial Deployment & Security

Deploying software directly onto OT/ICS networks requires strict operational measures:

* Restrict access to S7 TCP Port `102` using managed industrial firewalls or VLAN segmentation.
* Note that legacy S7comm is an unencrypted, unauthenticated protocol; do not route raw S7 traffic across untrusted or public networks.
* Refer to [docs/secure-deployment.md](https://www.google.com/search?q=docs/secure-deployment.md) for network hardening guidelines.

---

## 📄 License

This project is licensed under the **GNU Lesser General Public License v3.0 (LGPLv3)**.

See [LICENSE](https://www.google.com/search?q=LICENSE) and [lgpl-3.0.txt](https://www.google.com/search?q=lgpl-3.0.txt) for details.

---

## 🌐 Acknowledgments

* **Davide Nardella** – Creator and lead developer of the foundational [Snap7](https://www.google.com/search?q=https://snap7.sourceforge.net/) library.
* The **Open-Source Industrial Automation Community** for testing, protocol validation, and continuous field feedback.

```

```
