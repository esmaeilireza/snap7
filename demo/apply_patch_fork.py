with open("fork_bridge.py", "r", encoding="utf-8") as f:
    c = f.read()
consts = """
# --- DB1 Standardized Memory Map (byte offsets) ---
DB1_TEMP_OFFSET     = 0    # Real (4B) - Process temperature
DB1_CPU_OFFSET      = 4    # Real (4B) - CPU usage percent
DB1_RAM_OFFSET      = 8    # Real (4B) - RAM usage percent
DB1_SETPOINT_OFFSET = 12   # Real (4B) - Operator setpoint
DB1_HEARTBEAT_OFFSET= 16   # Byte (1B) - Heartbeat counter 0-255
"""
anchor = "P_U16_REMOTE_PORT = 2  # p_u16_RemotePort"
if "DB1_TEMP_OFFSET" not in c:
    c = c.replace(anchor, anchor + consts)
methods = """
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
"""
anchor2 = "    def disconnect(self):"
if "def read_byte" not in c:
    c = c.replace(anchor2, methods + "\n" + anchor2, 1)
with open("fork_bridge.py", "w", encoding="utf-8") as f:
    f.write(c)
print("fork_bridge.py patched")
