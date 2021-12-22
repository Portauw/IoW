from multiprocessing import Process, Event, Queue

from src.base import EdgiseBase
import grovepi


class VibrationSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, input_q: Queue, output_q: Queue, **kwargs):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._input_q: Queue = input_q
        self._output_q: Queue = output_q
        for key, val in kwargs.items():
            self.info("key: {} - value: {}".format(key,val))
            setattr(self, key, val)

        Process.__init__(self)
        EdgiseBase.__init__(self, name=self.name, logging_q=logging_q)
        # config = {
        #           "PINNR":int,
        #           "SensorI    bD":int,
        #           "Unit":"cm"
        #           "SensorType":""
        #           }

    def read_sensor(self):
        sensor_value = grovepi.analogRead(self.Pin)
        return sensor_value

    def run(self) -> None:
        self.info("Starting vibration sensor")
        grovepi.pinMode(self.Pin, self.Type)

        while not self._stop_event.is_set():
            if not self._input_q.empty():
                measurement_dict = self._input_q.get_nowait()

                raw_val = self.read_sensor()
                measurement = {
                    'RawVal': raw_val,
                }
                measurement_dict[self.name] = measurement
                self._output_q.put_nowait(measurement_dict)
