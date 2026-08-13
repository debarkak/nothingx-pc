import sys
from nothingx.device import Device
from nothingx.wire import Cmd, Dir
import time

d = Device.discover()

# Try payload 1
print("Trying payload: [0x02, 0x01, 0x00]")
d._session.send(Cmd.IN_EAR, Dir.SET, bytes([0x02, 0x01, 0x00]))
time.sleep(0.5)
print("Result:", d.inear.get())

# Try payload 2
print("Trying payload: [0x02, 0x01, 0x00, 0x02, 0x00]")
d._session.send(Cmd.IN_EAR, Dir.SET, bytes([0x02, 0x01, 0x00, 0x02, 0x00]))
time.sleep(0.5)
print("Result:", d.inear.get())

# Try payload 3
print("Trying payload: [0x01, 0x00, 0x00]")
d._session.send(Cmd.IN_EAR, Dir.SET, bytes([0x01, 0x00, 0x00]))
time.sleep(0.5)
print("Result:", d.inear.get())

