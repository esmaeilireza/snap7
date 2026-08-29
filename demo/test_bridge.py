import sys
sys.path.insert(0, '.')
import fork_bridge as fb

print("Ì¥å Initializing Fork Library...")
lib = fb.Snap7ForkLibrary()

print("Ì∫Ä Starting embedded server on port 4102...")
s = fb.ForkServer(lib)
ok = s.start(4102)
print(f"   Server started: {ok}")

print("Ì¥ó Connecting client to 127.0.0.1:4102...")
c = fb.ForkClient(lib)
ok2 = c.connect('127.0.0.1', 0, 1, 4102)
print(f"   Client connected: {ok2}")

print("Ì≥ù Writing 123.45 to DB1, Offset 0...")
c.write_real(1, 0, 123.45)

print("Ì≥ñ Reading back from DB1, Offset 0...")
val = c.read_real(1, 0)
print(f"   Read value: {val}")

print("Ì∑π Cleaning up...")
c.disconnect()
s.stop()
print("‚úÖ Done - clean shutdown!")
