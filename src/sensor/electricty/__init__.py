from math import sqrt
from typing import List
from multiprocessing import Process, Event, Queue
from src.base import EdgiseBase
import time
import json
import grovepi


class ACSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, input_q: Queue, output_q: Queue, config_json, **kwargs):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._input_q: Queue = input_q
        self._output_q: Queue = output_q
        self._output_q: Queue = output_q
        self.RMS_voltage = 230
        self._config = config_json
        self.info("{} -  type {}".format(self._config, type(self._config)))
        # for key, val in kwargs.items():
        #     self.info("key: {} - value: {}".format(key,val))
        #     setattr(self, key, val)

        Process.__init__(self, name="Ac")
        EdgiseBase.__init__(self, name="Electricity sensor", logging_q=logging_q)

        # config = {
        #           "name":str
        #           "PINNR":int,
        #           "SensorI    bD":int,
        #           "Unit":"cm"
        #           "SensorType":""
        #           }

    # def read_sensor(self):
    #     sensor_value = grovepi.analogRead(self._config['pin'])
    #     return sensor_value

    def amplitude_current(self, sensor_value):
        return float(sensor_value / 1024 * self.VCC / 800 * 2000000)

    def RMS_current(self, amplitude_current):
        return amplitude_current / sqrt(2)

    def avg_power_consumption(self, RMS_current):
        return self.RMS_voltage * RMS_current

    def run(self) -> None:
        self.info("Starting AC sensor")
        print(type(self._config))
        self._config.append(2)
        for i in self._config:
            print(i)
        #self.info("config: {}".format(self._config))
        #grovepi.pinMode(self._config['pin'], self._config['type'])

        while not self._stop_event.is_set():
            if not self._input_q.empty():
                measurement_dict = self._input_q.get_nowait()

                raw_val = self.read_sensor()
                amplitude_current = self.amplitude_current(raw_val)
                rms_current = self.RMS_current(amplitude_current)
                avg_power = self.avg_power_consumption(rms_current)
                measurement = {
                    'RawVal': raw_val,
                    'CurrentAmp': amplitude_current,
                    'RMSCurrent': rms_current,
                    'AVGPower': avg_power
                }
                #measurement_dict[self._config['name']] = measurement
                #self._output_q.put_nowait(measurement_dict)
