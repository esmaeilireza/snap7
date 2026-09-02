# Snap7 Qt Monitor & Diagnostic Station

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]()
[![Framework: PySide6](https://img.shields.io/badge/Framework-PySide6%20(Qt6)-green.svg)]()
[![Platform: Windows | Linux](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)]()

A high-performance, asynchronous desktop HMI and commissioning workbench for Siemens S7 PLCs, built with **PySide6 (Qt for Python)** and powered by the **Snap7** communication suite.

Designed for automation engineers and field technicians to monitor, test, and validate PLC Data Blocks (DB) during commissioning—without requiring heavy engineering suites (such as TIA Portal or Step 7).

---

## 📸 Overview

![HMI Monitor Screenshot](demo/screenshot.png)

---

## ⚙️ Key Capabilities

* **Asynchronous Polling Engine:** Background cyclic polling via dedicated worker threads (`QThread`), preventing UI freeze during heavy traffic or network delays.
* **Real-Time Data Block Decoding:** Live reading and structured parsing of S7 Data Blocks supporting standard types (`BOOL`, `INT`, `DINT`, `REAL`).
* **Hardware-Free Simulation:** Built-in dynamic mock server for offline commissioning, loopback testing, and UI demonstration without physical hardware.
* **Automatic Failover & Reconnection:** Graceful degradation to loopback simulation upon communication loss, with auto-recovery on link restoration.
* **High-Rate Telemetry Visualization:** Low-overhead, hardware-accelerated time-series plotting powered by `pyqtgraph`.
* **Diagnostic Console:** Color-coded protocol telemetry, time-stamped status messages, and operational event logging.
* **Persistent Configuration:** Quick runtime configuration for PLC Target IP, Rack, Slot, DB numbers, and update cycle intervals (`config.ini`).

---

## 🏗️ Architecture

The application cleanly decouples communication drivers from UI rendering to ensure deterministic polling and responsive operator controls:


```

┌─────────────────────────────────────────────────────────────┐
│                      PySide6 UI Layer                       │
│  (Views, Hardware-Accelerated Charts, Telemetry Cards)     │
└──────────────────────────────▲──────────────────────────────┘
│ Qt Signals / Slots
┌──────────────────────────────▼──────────────────────────────┐
│                    Worker Thread Engine                     │
│  (Non-blocking cyclic task, setpoint dispatch, watchdog)    │
└──────────────────────────────▲──────────────────────────────┘
│ C-types ABI
┌──────────────────────────────▼──────────────────────────────┐
│                     Snap7 Native Driver                     │
│               (snap7.dll / libsnap7.so)                     │
└──────────────────────────────▲──────────────────────────────┘
│ ISO-on-TCP (RFC 1006 / S7comm)
▼
Siemens PLC / Mock Server

```

---

## 🔌 PLC Compatibility

Compatible with any Siemens PLC supporting S7comm over ISO-on-TCP:

* **S7-300 / S7-400 / WinAC:** Full native support.
* **S7-1200 / S7-1500:** Supported with optimized block access disabled (Standard DB) and **"Permit access with PUT/GET communication"** enabled in the CPU hardware configuration.
* **Snap7 Mock Server:** Built-in loopback support.

---

## 🚀 Quick Start

### 1. Prerequisites

* Python **3.10** or higher.
* Compatible OS: Windows 10/11 (x64) or Linux (x86_64).

### 2. Installation

Clone the repository and install required dependencies:

```bash
git clone [https://github.com/esmaeilireza/snap7-qt-monitor.git](https://github.com/esmaeilireza/snap7-qt-monitor.git)
cd snap7-qt-monitor
pip install -r requirements.txt

```

### 3. Running in Simulation Mode (Offline)

Test the dashboard immediately without hardware:

```bash
python scada_dashboard.py --simulate

```

### 4. Running with the Dynamic Mock Server

Start the local mock server to simulate changing PLC registers:

```bash
python snap7_server.py

```

In a separate terminal, start the monitor station:

```bash
python scada_dashboard.py

```

Set the IP address to `127.0.0.1` (Rack: `0`, Slot: `2`) within the Settings tab to bind to the local server.

---

## 📁 Repository Structure

```
snap7-qt-monitor/
├── scada_dashboard.py       # Main application entry point
├── fork_bridge.py           # Typed Snap7 Python bridge & client abstraction
├── sensor_simulator.py      # Dynamic process variable generator
├── snap7_server.py          # Standalone S7 mock server (DB1 emulation)
├── test_bridge.py           # Unit tests and loopback validation
├── requirements.txt         # Runtime dependencies
├── config.ini               # Runtime persistent configuration
├── ui/                      # Modular UI components
│   ├── dashboard_ui.py      # Main window and layout orchestration
│   ├── chart_widget.py      # pyqtgraph real-time telemetry plotting
│   ├── status_cards.py      # KPI cards & state indicators
│   ├── asset_panel.py       # Station topology & target selector
│   ├── log_widget.py        # Real-time event & diagnostic terminal
│   ├── theme.py             # Dark industrial design palette
│   └── widgets.py           # Base UI primitives & controls
└── LICENSE                  # LGPL-3.0 license

```

---

## 🛠️ Configuration Guide

Default parameters can be adjusted via the UI Settings panel or directly in `config.ini`:

```ini
[PLC]
ip = 192.168.0.1
rack = 0
slot = 1
port = 102
polling_interval_ms = 100

[MAPPING]
db_number = 1
start_offset = 0
size = 64

```

---

## 📄 License

This project is licensed under the **GNU Lesser General Public License v3.0 (LGPLv3)** - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

---

## 🙏 Acknowledgments

* **Davide Nardella** for designing and maintaining the foundational [Snap7](https://www.google.com/search?q=https://snap7.sourceforge.net/) Ethernet communication library.
* The **Qt Company** for PySide6.
* The **pyqtgraph** team for providing low-overhead data visualization tools.

```

```
