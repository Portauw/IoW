from src.log import logger
from src.base import EdgiseBase
from multiprocessing import Queue

try:
    import serial
except Exception as e:
    print(
        f"While importing serial, an exception occured : {e}. This is normal if you are not running on a Raspberry Pi with pyserial")


class NextionDisplay(EdgiseBase):
    def __init__(self,
                 logging_q: Queue,
                 portname: str = "/dev/ttyAMA1",
                 baudrate: int = 9600,
                 timeout: float = 1.0):

        EdgiseBase.__init__(self, name="NEXTION", logging_q=logging_q)

        self._portname = portname
        self._baudrate = baudrate
        self._timeout = timeout
        self._end_of_command = bytes([255, 255, 255])
        self._port = self._port_factory()

    def _port_factory(self):
        return serial.Serial(port=self._portname, baudrate=self._baudrate, timeout=self._timeout)

    @property
    def portname(self):
        return self._portname

    @property
    def baudrate(self):
        return self._baudrate

    @baudrate.setter
    def baudrate(self, new_baud):
        self._baudrate = new_baud
        self._port = self._port_factory()
        pass

    @property
    def timeout(self):
        return self._timeout

    @property
    def port(self):
        return self._port

    @property
    def end_of_command(self):
        return self._end_of_command

    def send_cmd(self, cmd: str):
        # print(f"sending : {cmd}")
        self.port.write(cmd.encode("ascii") + self._end_of_command)

    def __str__(self):
        return f"Nextion @ {self._portname} | {self._baudrate}"
