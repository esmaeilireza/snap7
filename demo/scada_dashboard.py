#!/usr/bin/env python3
import sys
import time
import threading
import argparse
from pathlib import Path

# ---- DPI awareness (must be before any Tk import) ----
if sys.platform == 'win32':
    from ctypes import windll
    try:
        windll.shcore.SetProcessDpiAwareness(1)     # Windows 8.1+
    except Exception:
        try:
            windll.user32.SetProcessDPIAware()      # fallback for older
        except Exception:
            pass

# Now we can safely import tkinter and matplotlib
import tkinter as tk

sys.path.insert(0, str(Path(__file__).parent))

from ui.dashboard_ui import SCADADashboard
from fork_bridge import (Snap7ForkLibrary, ForkServer, ForkClient,
                         gather_build_info, ForkBuildError, DEFAULT_PORT,
                         DB1_TEMP_OFFSET, DB1_CPU_OFFSET, DB1_RAM_OFFSET,
                         DB1_SETPOINT_OFFSET, DB1_HEARTBEAT_OFFSET)
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


def main():
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

    # Apply Tk scaling to match system DPI
    root = tk.Tk()
    root.tk.call('tk', 'scaling', root.winfo_fpixels('1i') / 72.0)
    root.destroy()  # we only need the scaling value; will create real window later

    dashboard = SCADADashboard(
        client=reader_client, build_info=build_info, server_mode=server_mode,
        sensor_sim=TemperatureSensorSimulator(setpoint=65.5),
        system_sim=SystemMetricsSimulator(),
    )
    dashboard.log_message('INFO', 'FORK', f"Loaded {build_info['dll_rel']}")
    dashboard.log_message('INFO', 'FORK', f"sha256={build_info['dll_sha']} commit={build_info['commit']}")

    def teardown():
        stop_event.set()
        for c in (reader_client, writer_client):
            if c:
                try: c.close()
                except Exception: pass
        if server:
            try: server.stop()
            except Exception: pass

    dashboard.on_shutdown = teardown
    try:
        dashboard.mainloop()
    finally:
        teardown()
        print("[OK] Shutdown complete.")


if __name__ == "__main__":
    main()