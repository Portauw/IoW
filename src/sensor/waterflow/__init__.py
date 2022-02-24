from multiprocessing import Process, Event, Queue, Lock

from src.base import EdgiseBase

import RPi.GPIO as GPIO
import time
from config import cfg
import sys


class WaterflowSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, input_q: Queue, output_q: Queue,
                 config_dict, resource_lock: Lock, **kwargs):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._input_q: Queue = input_q
        self._output_q: Queue = output_q
        self._config_dict = config_dict
        self._name = self._config_dict['name']
        self.pulse_count=0
        self.start_counter=0

        Process.__init__(self)
        EdgiseBase.__init__(self, name=name, logging_q=logging_q)

        # config = {
        #           "PINNR":int,
        #           "SensorI    bD":int,
        #           "Unit":"cm"
        #           "SensorType":""
        #           }

    def count_sensor_pulse(self):
        if self.start_counter:
            self.pulse_count += 1

    def run(self) -> None:
        self.info("Starting Waterflow sensor")
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._config_dict['Pin'], GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.add_event_detect(self._config_dict['Pin'], GPIO.FALLING, callback=self.count_sensor_pulse)

        while not self._stop_event.is_set():
            if not self._input_q.empty():
                measurement_dict = self._input_q.get_nowait()
                self.start_counter = 1
                time.sleep(1)
                self.start_counter = 0
                raw_val = self.pulse_count
                flow_s = (raw_val/396)
                flow_min = (raw_val/6.6)
                flow_h = (raw_val*60)/6.6
                self.pulse_count=0
                self.print(self._config_dict['name'])
                self.info("Raw Value: {}".format(raw_val))

                measurement = {
                    'RawVal': raw_val,
                    'flowSec': flow_s,
                    'flowMin': flow_min,
                    'flowHour': flow_h
                }
                measurement_dict[self._config_dict['name']] = measurement
                self._output_q.put_nowait({'event':json.dumps(measurement)})
                time.sleep(1)
