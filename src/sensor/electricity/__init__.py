import time
import json

from math import sqrt
from typing import List
from multiprocessing import Process, Event, Queue
from src.base import EdgiseBase
from grove.adc import ADC


class ACSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, input_q: Queue, output_q: Queue, config_json: str,
                 config_dict, **kwargs):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._input_q: Queue = input_q
        self._output_q: Queue = output_q
        self._output_q: Queue = output_q
        self.RMS_voltage = 230
        self.VCC = 5
        self._config_json: str = config_json
        self._config_dict = config_dict
        self._name = self._config_dict['name']
        self.info("{} -  type {}".format(self._config_json, type(self._config_json)))
        self.adc = ADC()
        Process.__init__(self)
        EdgiseBase.__init__(self, name=self._name, logging_q=logging_q)

        # config = {
        #           "name":str
        #           "PINNR":int,
        #           "SensorI    bD":int,
        #           "Unit":"cm"
        #           "SensorType":""
        #           }

    def read_sensor(self):
        sensor_value = adc.read(self._config_dict['pin'])
        return sensor_value

    def amplitude_current(self, sensor_value):
        return float(sensor_value / 1024 * self.VCC / 800 * 2000000)

    def RMS_current(self, amplitude_current):
        return amplitude_current / sqrt(2)

    def avg_power_consumption(self, RMS_current):
        return self.RMS_voltage * RMS_current

    def run(self) -> None:
        self.info("Starting AC sensor")
        print(type(self._config_json))
        print(type(self._config_dict))
        print(self._config_dict['name'])
        config = json.loads(self._config_json)
        print(type(config))
        for k, v in config.items():
            print(v)

        while not self._stop_event.is_set():
            if not self._input_q.empty():
                measurement_dict = self._input_q.get_nowait()

                raw_val = self.read_sensor()
                self.info("Raw Value: {}".format(raw_val))
                amplitude_current = self.amplitude_current(raw_val)
                self.info("A I Value: {}".format(amplitude_current))
                rms_current = self.RMS_current(amplitude_current)
                self.info("RMS I Value: {}".format(rms_current))
                avg_power = self.avg_power_consumption(rms_current)
                self.info("AVG W Value: {}".format(avg_power))

                measurement = {
                    'RawVal': raw_val,
                    'CurrentAmp': amplitude_current,
                    'RMSCurrent': rms_current,
                    'AVGPower': avg_power
                }
                measurement_dict[self._config_dict['name']] = measurement
                self._output_q.put_nowait(measurement_dict)
