#!/usr/bin/env python3
"""
S7 SCADA - Fork-Integrated Industrial Dashboard
Fixed: Function naming, DPI awareness, font resolution, safe shutdown,
       deferred initial log messages.
"""
import sys
import time
import threading
import argparse
from pathlib import Path

# ---- DPI awareness (must be before any Tk import) ----
if sys.platform == 'win32':
    from ctypes import windll
    try:
        windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                windll.user32.SetProcessDPIAware()
            except Exception:
                pass

import tkinter as tk
from tkinter import font as tkfont

sys.path.insert(0, str(Path(__file__).parent))

from ui.dashboard_ui import SCADADashboard
from fork_bridge import (
    Snap7ForkLibrary, ForkServer, ForkClient,
    gather_build_info, ForkBuildError, DEFAULT_PORT,
    DB1_TEMP_OFFSET, DB1_CPU_OFFSET, DB1_RAM_OFFSET,
    DB1_SETPOINT_OFFSET, DB1_HEARTBEAT_OFFSET,
)
from sensor_simulator import TemperatureSensorSimulator, SystemMetricsSimulator


def parse_arguments():
    p = argparse.ArgumentParser(description='S7 SCADA Fork-Integrated Dashboard')
    p.add_argument('--simulate', '-s', action='store_true', help='UI-only simulation')
    p.add_argument('--ip', default='127.0.0.1')
    p.add_argument('--rack', type=int, default=0)
    p.add_argument('--slot', type=int, default=1)
    p.add_argument('--port', type=int, default=DEFAULT_PORT)
    return p.parse_args()


def start_plc_simulation_worker(writer_client, sensor_sim, system_sim, stop_event):
    def run():
        heartbeat = 0
        while not stop_event.is_set():
            try:
                temp_val = sensor_sim.read()
                metrics = system_sim.get_metrics()
                writer_client.write_real(1, DB1_TEMP_OFFSET, float(temp_val))
                writer_client.write_real(1, DB1_CPU_OFFSET, float(metrics['cpu']))
                writer_client.write_real(1, DB1_RAM_OFFSET, float(metrics['memory']))
                heartbeat = (heartbeat + 1) % 256
                writer_client.write_byte(1, DB1_HEARTBEAT_OFFSET, heartbeat)
                time.sleep(0.5)
            except Exception as ex:
                print(f"[Worker Error] {ex}")
                time.sleep(1)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t


def _resolve_font_family(preferred: str) -> str:
    """Return preferred font if available, otherwise best system fallback."""
    root_probe = tk.Tk()
    root_probe.withdraw()
    available = set(tkfont.families(root_probe))
    root_probe.destroy()

    fallback_chain = [
        preferred,
        'Segoe UI',
        'Tahoma',
        'Arial',
        'sans-serif',
    ]
    for family in fallback_chain:
        if family in available:
            return family
    return 'Arial'


def main():
    # 🔧 FIX: Changed parse_args() to parse_arguments() to match definition
    args = parse_arguments() 
    
    print("=" * 70)
    print("  S7 SCADA - Fork-Integrated Industrial Dashboard")
    print("=" * 70)
    
    stop_event = threading.Event()
    lib, server, reader_client, writer_client, worker = None, None, None, None, None
    server_mode = "UI SIMULATION (no protocol)"

    if not args.simulate:
        try:
            lib = Snap7ForkLibrary()
            print(f"[OK] Loaded fork DLL : {lib.path}")
        except ForkBuildError as e:
            print(f"[ERR] {e}")
            if input("Run UI-only simulation instead? [Y/n]: ").lower() == 'n':
                sys.exit(1)

    if lib:
        server = ForkServer(lib)
        if server.start(args.port):
            server_mode = f"EMBEDDED (fork Srv_* on TCP {args.port})"
            print(f"[OK] Embedded fork server on TCP {args.port}")
        else:
            server_mode = "EXTERNAL (port busy)"
            print("[WARN] Port busy - using existing server")

        writer_client = ForkClient(lib)
        if not writer_client.connect(args.ip, args.rack, args.slot, args.port):
            print("[ERR] Writer client failed")
            writer_client = None

        reader_client = ForkClient(lib)
        if reader_client.connect(args.ip, args.rack, args.slot, args.port):
            print(f"[OK] Reader client connected to {args.ip}")
            reader_client.write_real(1, DB1_SETPOINT_OFFSET, 65.5)
        else:
            print("[ERR] Reader client failed")
            reader_client = None

        if writer_client:
            worker = start_plc_simulation_worker(
                writer_client, TemperatureSensorSimulator(setpoint=65.5),
                SystemMetricsSimulator(), stop_event)
            print("[OK] Data feeder worker started (2 Hz)")

    build_info = gather_build_info(lib.path if lib else None)
    print(f"[INFO] branch={build_info['branch']} commit={build_info['commit']} sha256={build_info['dll_sha']}")

    resolved_font = _resolve_font_family('Segoe UI Variable')
    print(f"[INFO] Resolved UI font: {resolved_font}")

    probe = tk.Tk()
    probe.withdraw()
    dpi_scale = probe.winfo_fpixels('1i') / 72.0
    probe.tk.call('tk', 'scaling', dpi_scale)
    probe.withdraw()
    probe.update_idletasks()
    probe.destroy()

    dashboard = SCADADashboard(
        client=reader_client, build_info=build_info, server_mode=server_mode,
        sensor_sim=TemperatureSensorSimulator(setpoint=65.5),
        system_sim=SystemMetricsSimulator(),
        resolved_font=resolved_font,
    )
    

    # FIX: Defer log messages until after mainloop starts processing events.
    # Previously these were called synchronously before mainloop(), which
    # meant the Treeview widget existed but wasn't rendered yet.
    def inject_startup_logs():
        dashboard.log_message('INFO', 'FORK', f"Loaded {build_info.get('dll_rel', 'n/a')}")
        dashboard.log_message('INFO', 'FORK', f"sha256={build_info.get('dll_sha', 'n/a')} commit={build_info.get('commit', 'n/a')}")
        dashboard.log_message('INFO', 'SYSTEM', 'Dashboard initialized successfully.')
        dashboard.log_message('INFO', 'SYSTEM', f"Server mode: {server_mode}")

    dashboard.after(300, inject_startup_logs)

    def teardown():
        stop_event.set()
        for c in (reader_client, writer_client):
            if c:
                try:
                    c.close()
                except Exception:
                    pass
        if server:
            try:
                server.stop()
            except Exception:
                pass

    dashboard.on_shutdown = teardown
    try:
        dashboard.mainloop()
    finally:
        teardown()
        print("[OK] Shutdown complete.")


if __name__ == "__main__":
    main()