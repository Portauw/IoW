from multiprocessing import Process, Event, Queue

from src.base import EdgiseBase


class WaterflowSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, input_q: Queue, output_q: Queue, name: str, **kwargs):
        self._sensor_name: str = name
        self._config:dict = config
        self._logging_q: Queue = logging_q
        self._input_q: Queue = input_q
        self._output_q: Queue = output_q
        for key, val in kwargs.items():
            setattr(self, key, val)

        Process.__init__(self)
        EdgiseBase.__init__(self, name=name, logging_q=logging_q)

        # config = {
        #           "PINNR":int,
        #           "SensorI    bD":int,
        #           "Unit":"cm"
        #           "SensorType":""
        #           }

    def read_sensor(self):
        pass

    def run(self) -> None:
        pass
