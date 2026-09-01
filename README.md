```markdown
# Snap7 – Industrial Communication Toolkit

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](gpl.txt)
[![CI](https://github.com/SCADACS/snap7/actions/workflows/smoke-test.yml/badge.svg)](https://github.com/SCADACS/snap7/actions)

This is a **community‑maintained fork** of the original [Snap7](http://snap7.sourceforge.net/) project.  
It extends the core library with features that make it easier to build **software PLCs, modern SCADA interfaces, and data‑driven industrial applications**.

---

## 🎯 Why This Fork?

Industrial automation code is often written **without** modern software practices – no version control, no automated testing, no security audits.  
This fork bridges that gap by adding:

- ✅ **Program block management** – upload, download, and list blocks programmatically.
- ✅ **Dynamic SZL support** – query system status lists for diagnostics.
- ✅ **Variable watching & monitor mode** – real‑time debugging.
- ✅ **A full Python/Tkinter dashboard** – a live SCADA‑like UI with charts, asset tables, and alarms (see below).

The goal is to make industrial code **as reliable and maintainable** as modern web applications.

---

## 🚀 Live Dashboard Demo

This repository includes a **Python‑based SCADA dashboard** that connects to any Snap7 server (real PLC or simulation).

### Quick Start (Simulation Mode)

```bash
cd demo
pip install -r requirements.txt   # (if you have a requirements file)
python scada_dashboard.py --simulate
```

You’ll see a live dashboard with:

- Real‑time temperature chart
- Asset table (list of connected PLCs/sensors)
- Communication log
- Alarm management
- Trends and reports

![Dashboard Screenshot](docs/dashboard.png)

> *Screenshot placeholder – replace with an actual image of your working dashboard.*

---

## 📁 Project Structure (Simplified)

📦 snap7/
├── 📂 demo/                          # 🚀 Your custom Python SCADA dashboard
│   ├── 🐍 scada_dashboard.py         # Main entry point
│   ├── 🧩 fork_bridge.py             # Snap7 client/server bridge
│   ├── 📡 sensor_simulator.py        # Simulated PLC data generator
│   ├── 🧪 test_bridge.py             # Unit tests for the bridge
│   ├── 🔧 apply_patch_fork.py        # Utility to apply custom patches
│   ├── ⚙️ run_dashboard.bat          # Windows launcher
│   ├── 📋 requirements.txt           # Python dependencies
│   └── 📂 ui/                        # User Interface components
│       ├── __init__.py
│       ├── asset_panel.py            # Connected assets list
│       ├── chart_widget.py           # Live temperature chart
│       ├── dashboard_ui.py           # Main dashboard layout
│       ├── log_widget.py             # Communication log
│       ├── status_cards.py           # System status & connection cards
│       ├── theme.py                  # Dark industrial color theme
│       ├── views.py                  # ViewManager + all views
│       └── widgets.py                # Reusable UI widgets (LEDs, badges, etc.)

├── 📂 src/                           # 🔧 Core Snap7 C++ source code
│   ├── 📂 core/                      # S7 protocol implementation
│   │   ├── s7_client.cpp/h
│   │   ├── s7_server.cpp/h
│   │   ├── s7_partner.cpp/h
│   │   ├── s7_peer.cpp/h
│   │   ├── s7_isotcp.cpp/h
│   │   ├── s7_micro_client.cpp/h
│   │   ├── s7_text.cpp/h
│   │   └── s7_types.h
│   ├── 📂 lib/                       # Library entry point
│   │   ├── snap7.def
│   │   ├── snap7_libmain.cpp
│   │   └── snap7_libmain.h
│   └── 📂 sys/                       # Platform abstraction layer
│       ├── snap_msgsock.cpp/h
│       ├── snap_sysutils.cpp/h
│       ├── snap_tcpsrvr.cpp/h
│       ├── snap_threads.cpp/h
│       ├── sol_threads.h
│       ├── unix_threads.h
│       └── win_threads.h

├── 📂 docs/                          # 📖 Additional documentation
│   ├── secure-deployment.md
│   └── industrial-networking.md

├── 📄 README.md                      # Project overview & quick start
├── 📄 SECURITY.md                    # Security guidelines
├── 📄 gpl.txt                        # GPL license text
├── 📄 lgpl-3.0.txt                   # LGPLv3 license text
├── 📄 HISTORY.txt                    # Version history
├── 📄 .gitignore                     # Ignored files for Git
├── 🔧 win-clean.bat                  # Clean build artifacts (Windows)
├── 🔧 final_fix.sh                   # Final touch-up script (Linux/macOS)
└── 📂 tools/                         # (optional) Auxiliary scripts
```

---

## 📦 Installation

### Pre‑built Binaries

Download the latest release package from the [Releases](https://github.com/SCADACS/snap7/releases) page.  
Unpack the archive – no installation required; all paths are relative.

**Platform‑specific files:**

| Platform | Library Location |
|----------|------------------|
| Windows 32‑bit | `release/Windows/Win32/snap7.dll` |
| Windows 64‑bit | `release/Windows/Win64/snap7.dll` |
| Linux x86_64   | `release/Linux/x86_64/libsnap7.so` |
| ARMv7 (RPi)    | `release/Linux/arm_v7/libsnap7.so` |

Copy the appropriate library to your system library path or to your application directory.

---

## 🔧 Building from Source

### Prerequisites

- **Linux (Ubuntu/Debian)**: `sudo apt-get install build-essential`
- **Windows (MSYS2)**: Install [MSYS2](https://www.msys2.org/), then run:

  ```bash
  pacman -S --needed mingw-w64-x86_64-gcc mingw-w64-x86_64-binutils make
  ```

### Build the Core Library

- **Linux**:

  ```bash
  cd build/unix
  make -f x86_64_linux.mk
  ```

- **Windows (MinGW64)**:

  ```bash
  cd build/windows/MinGW64
  make
  ```

### Build & Run the Loopback Test

```bash
cd examples/cpp/<your-platform>
make
./loopback_test
```

---

## 🔌 Using the Python Wrapper

The easiest way to interact with Snap7 from Python is to use the included dashboard code as a reference.  
A simple client example:

```python
from demo.fork_bridge import ForkClient  # or use the original snap7 library

client = ForkClient()
client.connect("192.168.1.1", 0, 1)
data = client.db_read(1, 0, 100)
client.disconnect()
```

For a full‑featured UI, run the dashboard as described above.

---

##  Continuous Integration

GitHub Actions automates:

- **Smoke tests** – builds and runs loopback tests on Ubuntu & Windows.
- **CodeQL** – security and quality analysis for C/C++.
- **Stale bot** – keeps the issue tracker tidy.

---

## 🔐 Security

When deploying in industrial environments, please review:

- [SECURITY.md](SECURITY.md)
- [docs/secure-deployment.md](docs/secure-deployment.md)
- [docs/industrial-networking.md](docs/industrial-networking.md)

---

## 📄 License

This project is licensed under the **GNU Lesser General Public License v3.0** – see the [LGPL-3.0](lgpl-3.0.txt) and [GPL](gpl.txt) files for details.

---

## 🙌 Contributing

Contributions are welcome!  
Please open an issue or pull request for bug fixes, new features, or documentation improvements.

---

## 🌐 Acknowledgments

- Original Snap7 authors – for the excellent library.
- The industrial automation community – for real‑world feedback and inspiration.
