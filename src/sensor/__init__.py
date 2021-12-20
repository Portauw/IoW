from multiprocessing import Process, Event, Queue

from src.base import EdgiseBase
import abc


class Sensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, input_q: Queue, output_q: Queue, name: str, config: dict):
        self._sensor_name: str = name
        self._config:dict = config
        self._logging_q: Queue = logging_q
        self._input_q: Queue = input_q
        self._output_q: Queue = output_q
        Process.__init__(self, name=name)
        EdgiseBase.__init__(self, name=name, logging_q=logging_q)

        # config = {
        #           "PINNR":int,
        #           "SensorI    bD":int,
        #           "Unit":"cm"
        #           "SensorType":""
        #           }

    @abc.abstractmethod
    def read_sensor(self):
        pass

    @abc.abstractmethod
    def run(self) -> None:
        pass
