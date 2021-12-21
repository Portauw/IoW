from multiprocessing import Process, Event, Queue

from src.base import EdgiseBase
import smbus2
import bme280


class EnvironmentSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, input_q: Queue, output_q: Queue, config: dict):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._input_q: Queue = input_q
        self._output_q: Queue = output_q
        self._config: dict = config
        self._output_q: Queue = output_q

        Process.__init__(self)
        EdgiseBase.__init__(self, name="Environment Sensor", logging_q=logging_q)

    def read_sensor(self):
        return bme280.sample(self._bus, self._address)

    def run(self) -> None:
        self.info("Starting vibration sensor")
        self._bus = smbus2.SMBus(self._config["port"])
        self._address = self._config["Address"]
        try:
            bme280.load_calibration_params(self._bus, )
        except:  # noqa: E722
            pass

        while not self._stop_event.is_set():
            if not self._input_q.empty():
                measurement_dict = self._input_q.get_nowait()

                raw_val = self.read_sensor()
                self.info(raw_val)
                measurement = {
                    "Temperature": raw_val.temperature,
                    "Pressure": raw_val.pressure,
                    "Humidity": raw_val.humidity
                }
                measurement_dict[self._config["name"]] = measurement
                self._output_q.put_nowait(measurement_dict)
