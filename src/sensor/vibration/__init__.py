from multiprocessing import Process, Event, Queue, Lock
import time
from src.base import EdgiseBase
from grove.adc import ADC


class VibrationSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, input_q: Queue, output_q: Queue, config_dict, resource_lock: Lock, **kwargs):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._input_q: Queue = input_q
        self._output_q: Queue = output_q
        self._config_dict = config_dict
        self.adc = ADC()
        self.i2c_lock = resource_lock

        Process.__init__(self)
        EdgiseBase.__init__(self, name=self._config_dict['name'], logging_q=logging_q)
        # config = {
        #           "PINNR":int,
        #           "SensorI    bD":int,
        #           "Unit":"cm"
        #           "SensorType":""
        #           }

    def read_sensor(self):
        sensor_value = self.adc.read(self._config_dict['pin'])
        return sensor_value

    def run(self) -> None:
        self.info("Starting vibration sensor")

        while not self._stop_event.is_set():
            if not self._input_q.empty():
                measurement_dict = self._input_q.get_nowait()
                self.i2c_lock.acquire()
                try:
                    raw_val = self.read_sensor()
                finally:
                    self.i2c_lock.release()
                self.info("Raw Value Vibration: {}".format(raw_val))
                measurement = {
                    'RawVal': raw_val,
                }
                measurement_dict[self._config_dict['name']] = measurement
                self._output_q.put_nowait(measurement_dict)
                time.sleep(2)
