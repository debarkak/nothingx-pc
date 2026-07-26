import time
from ..wire import Cmd, Dir, Earbud, State


class FindCommands:
    def __init__(self, session):
        self._s = session

    def _ring(self, earbud: int, state: int):
        self._s.run(Cmd.FIND_MY, Dir.SET, bytes([earbud, state]))

    def left(self):  self._ring(Earbud.LEFT, State.ON)
    def right(self): self._ring(Earbud.RIGHT, State.ON)

    def both(self):
        self.left()
        time.sleep(0.1)
        self.right()

    def stop(self):
        self._ring(Earbud.LEFT, State.OFF)
        time.sleep(0.1)
        self._ring(Earbud.RIGHT, State.OFF)
