from multiprocessing import Process, Event, Queue

from src.base import EdgiseBase
import grovepi

class VibrationSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, input_q: Queue, output_q: Queue, **config: dict):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._input_q: Queue = input_q
        self._output_q: Queue = output_q
        self._config: dict = config
        self._output_q: Queue = output_q

        Process.__init__(self)
        EdgiseBase.__init__(self, name="Vibration sensor", logging_q=logging_q)
        # config = {
        #           "PINNR":int,
        #           "SensorI    bD":int,
        #           "Unit":"cm"
        #           "SensorType":""
        #           }

    def read_sensor(self):
        sensor_value = grovepi.analogRead(self._config['Pin'])
        return sensor_value

    def run(self) -> None:
        self.info("Starting vibration sensor")
        grovepi.pinMode(self._config['Pin'], self._config['Type'])

        while not self._stop_event.is_set():
            if not self._input_q.empty():
                measurement_dict = self._input_q.get_nowait()

                raw_val = self.read_sensor()
                measurement = {
                    'RawVal': raw_val,
                }
                measurement_dict[self._config['name']] = measurement
                self._output_q.put_nowait(measurement_dict)

