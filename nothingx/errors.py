class NothingError(Exception):
    pass

class DeviceNotFoundError(NothingError):
    pass

class ConnectionError(NothingError):
    pass

class ProtocolError(NothingError):
    pass

class TimeoutError(NothingError):
    pass
