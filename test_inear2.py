import sys
from nothingx.device import Device
from nothingx.wire import Cmd, Dir
import time

d = Device.discover()
print("Initial:", d.inear.get())

d._session.send(Cmd.IN_EAR, Dir.SET, bytes([0x02, 0x01, 0x00]))
time.sleep(1)
res = d.inear.get()
print("After [0x02, 0x01, 0x00] (expect OFF):", res)

d._session.send(Cmd.IN_EAR, Dir.SET, bytes([0x02, 0x01, 0x01]))
time.sleep(1)
res = d.inear.get()
print("After [0x02, 0x01, 0x01] (expect ON):", res)

