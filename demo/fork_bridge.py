"""
ForkBridge - Deep integration with THIS repository's compiled artifacts.

Loads the snap7.dll that was compiled FROM THIS REPO's patched sources
using pure ctypes. No third-party wrapper (python-snap7) is involved, so
every byte travelling over ISO-on-TCP is produced by the fork's own code.

Both ends of the wire (Srv_* server and Cli_* client) run from the same
fork-built DLL.
"""
import ctypes
import hashlib
import struct
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SRV_AREA_DB = 5            # from s7_server.h: const int srvAreaDB = 5
DEFAULT_PORT = 102
P_U16_LOCAL_PORT = 1   # p_u16_LocalPort
P_U16_REMOTE_PORT = 2  # p_u16_RemotePort
# --- DB1 Standardized Memory Map (byte offsets) ---
DB1_TEMP_OFFSET     = 0    # Real (4B) - Process temperature
DB1_CPU_OFFSET      = 4    # Real (4B) - CPU usage percent
DB1_RAM_OFFSET      = 8    # Real (4B) - RAM usage percent
DB1_SETPOINT_OFFSET = 12   # Real (4B) - Operator setpoint
DB1_HEARTBEAT_OFFSET= 16   # Byte (1B) - Heartbeat counter 0-255
         # ISO-on-TCP / S7comm


class ForkBuildError(RuntimeError):
    pass


def find_fork_dll():
    """Locate the DLL compiled from this repo's sources."""
    candidates = [
        REPO_ROOT / "build" / "bin" / "Legacy" / "win64" / "snap7.dll",
        REPO_ROOT / "build" / "bin" / "win64" / "snap7.dll",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def sha256_short(path, n=12):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:n]


def git(*args):
    try:
        out = subprocess.run(["git", "-C", str(REPO_ROOT), *args],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def gather_build_info(dll_path):
    """Fingerprint of the fork build the dashboard is running."""
    return {
        "upstream": "SCADACS/snap7 v1.4.0",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD") or "n/a",
        "commit": git("rev-parse", "--short", "HEAD") or "n/a",
        "dll_rel": str(dll_path.relative_to(REPO_ROOT)) if dll_path else "n/a",
        "dll_sha": sha256_short(dll_path) if dll_path else "n/a",
    }


class Snap7ForkLibrary:
    """ctypes binding to the fork's own snap7.dll."""

    def __init__(self, dll_path=None):
        self.path = dll_path or find_fork_dll()
        if not self.path:
            raise ForkBuildError(
                "fork snap7.dll not found.\n"
                "Build it first (MSYS2 MinGW64):\n"
                "  cd build/windows/MinGW64 && make")
        self.cdll = ctypes.CDLL(str(self.path))
        self._prototypes()

    def _prototypes(self):
        L = self.cdll
        V, I = ctypes.c_void_p, ctypes.c_int
        # ---- Client API ----
        L.Cli_Create.restype = V
        L.Cli_Destroy.argtypes = [ctypes.POINTER(V)]
        L.Cli_ConnectTo.argtypes = [V, ctypes.c_char_p, I, I]
        L.Cli_ConnectTo.restype = I
        L.Cli_Disconnect.argtypes = [V]; L.Cli_Disconnect.restype = I
        L.Cli_DBRead.argtypes = [V, I, I, I, V]; L.Cli_DBRead.restype = I
        L.Cli_DBWrite.argtypes = [V, I, I, I, V]; L.Cli_DBWrite.restype = I
        L.Cli_GetConnected.argtypes = [V, ctypes.POINTER(I)]
        L.Cli_GetConnected.restype = I
        L.Cli_ErrorText.argtypes = [I, ctypes.c_char_p, I]
        L.Cli_ErrorText.restype = I
        # ---- Server API ----
        L.Srv_Create.restype = V
        W = ctypes.c_uint16
        L.Srv_RegisterArea.argtypes = [V, I, W, V, I]  # Index is word, before pointer
        L.Srv_RegisterArea.restype = I
        L.Srv_StartTo.argtypes = [V, ctypes.c_char_p]  # Takes Address string, not port int
        L.Srv_StartTo.restype = I
        L.Srv_SetParam.argtypes = [V, I, V]
        L.Srv_SetParam.restype = I
        L.Cli_SetParam.argtypes = [V, I, V]
        L.Cli_SetParam.restype = I
        L.Srv_Stop.argtypes = [V]; L.Srv_Stop.restype = I
        L.Srv_Destroy.argtypes = [ctypes.POINTER(V)]
        # Added for server errors
        L.Srv_ErrorText.argtypes = [I, ctypes.c_char_p, I]
        L.Srv_ErrorText.restype = I

    def error_text(self, code):
        buf = ctypes.create_string_buffer(1024)
        self.cdll.Cli_ErrorText(code, buf, 1024)
        return buf.value.decode("latin-1")

    def server_error_text(self, code):
        buf = ctypes.create_string_buffer(1024)
        self.cdll.Srv_ErrorText(code, buf, 1024)
        return buf.value.decode("latin-1")


class ForkServer:
    """Embedded S7 server running from the fork's DLL."""

    def __init__(self, lib, db_size=256):
        self.lib = lib
        self.db1 = (ctypes.c_ubyte * db_size)()   # must stay alive
        self.handle = None
        self.port = None

    def start(self, port=DEFAULT_PORT, address="127.0.0.1"):
        L = self.lib.cdll
        self.handle = L.Srv_Create()
        if not self.handle:
            raise ForkBuildError("Srv_Create returned NULL handle")

        # Correct order: AreaCode, Index (word), Pointer, Size
        rc = L.Srv_RegisterArea(self.handle, SRV_AREA_DB, 1, 
                                ctypes.cast(self.db1, ctypes.c_void_p), 
                                ctypes.sizeof(self.db1))
        if rc != 0:
            err_msg = self.lib.server_error_text(rc)
            raise ForkBuildError(f"Srv_RegisterArea failed (rc={rc}): {err_msg}")

        # Set Port if not default 102
        if port != 102:
            p = ctypes.c_uint16(port)
            rc = L.Srv_SetParam(self.handle, P_U16_LOCAL_PORT, ctypes.byref(p))
            if rc != 0:
                 raise ForkBuildError(f"Srv_SetParam failed: {self.lib.server_error_text(rc)}")

        # Start with Address string
        rc = L.Srv_StartTo(self.handle, address.encode("ascii"))
        if rc != 0:
            return False
        self.port = port
        return True

    def stop(self):
        if self.handle:
            try:
                self.lib.cdll.Srv_Stop(self.handle)
            except OSError:
                pass  # Server threads may have already cleaned up
            try:
                h = ctypes.c_void_p(self.handle)
                self.lib.cdll.Srv_Destroy(ctypes.byref(h))
            except OSError:
                pass  # Handle may already be invalid after stop
            self.handle = None


class ForkClient:
    """S7 client running from the fork's DLL with configurable timeouts."""

    # Snap7 parameter codes for timeouts (verified from snap7.h)
    P_SEND_TIMEOUT = 4   # p_i32_SendTimeout
    P_RECV_TIMEOUT = 5   # p_i32_RecvTimeout

    def __init__(self, lib):
        self.lib = lib
        self.handle = lib.cdll.Cli_Create()

    def set_timeouts(self, send_ms=1000, recv_ms=1000):
        """Set send and receive timeouts in milliseconds.
        This prevents the client from blocking indefinitely on dead PLCs.
        """
        if self.handle:
            v = ctypes.c_int(send_ms)
            self.lib.cdll.Cli_SetParam(self.handle, self.P_SEND_TIMEOUT, ctypes.byref(v))
            v = ctypes.c_int(recv_ms)
            self.lib.cdll.Cli_SetParam(self.handle, self.P_RECV_TIMEOUT, ctypes.byref(v))

    def connect(self, ip="127.0.0.1", rack=0, slot=1, port=DEFAULT_PORT):
        if port != 102:
            p = ctypes.c_uint16(port)
            self.lib.cdll.Cli_SetParam(self.handle, P_U16_REMOTE_PORT, ctypes.byref(p))
        rc = self.lib.cdll.Cli_ConnectTo(self.handle, ip.encode(), rack, slot)
        return rc == 0

    def connected(self):
        v = ctypes.c_int(0)
        self.lib.cdll.Cli_GetConnected(self.handle, ctypes.byref(v))
        return bool(v.value)

    def read_real(self, db, offset):
        buf = (ctypes.c_ubyte * 4)()
        rc = self.lib.cdll.Cli_DBRead(self.handle, db, offset, 4,
                                      ctypes.cast(buf, ctypes.c_void_p))
        if rc != 0:
            raise ForkBuildError(self.lib.error_text(rc))
        return struct.unpack(">f", bytes(buf))[0]   # S7 REAL = big-endian IEEE754

    def write_real(self, db, offset, value):
        buf = (ctypes.c_ubyte * 4)(*struct.pack(">f", value))
        rc = self.lib.cdll.Cli_DBWrite(self.handle, db, offset, 4,
                                       ctypes.cast(buf, ctypes.c_void_p))
        return rc == 0

    def read_byte(self, db, offset):
        buf = (ctypes.c_ubyte * 1)()
        rc = self.lib.cdll.Cli_DBRead(self.handle, db, offset, 1,
                                      ctypes.cast(buf, ctypes.c_void_p))
        if rc != 0:
            raise ForkBuildError(self.lib.error_text(rc))
        return buf[0]

    def write_byte(self, db, offset, value):
        buf = (ctypes.c_ubyte * 1)(int(value) & 0xFF)
        rc = self.lib.cdll.Cli_DBWrite(self.handle, db, offset, 1,
                                       ctypes.cast(buf, ctypes.c_void_p))
        return rc == 0

    def close(self):
        """Safely disconnect and destroy the client handle."""
        if self.handle:
            try:
                self.lib.cdll.Cli_Disconnect(self.handle)
            except OSError:
                pass  # already disconnected
            try:
                h = ctypes.c_void_p(self.handle)
                self.lib.cdll.Cli_Destroy(ctypes.byref(h))
            except OSError:
                pass  # handle may already be invalid
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()