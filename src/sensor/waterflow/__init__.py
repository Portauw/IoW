import json
from multiprocessing import Process, Event, Queue, Lock

from src.base import EdgiseBase

import RPi.GPIO as GPIO
import time


def count_sensor_pulse(counter_tuple):
    if counter_tuple[0]:
        counter_tuple[1] += 1


class WaterflowSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, output_q: Queue,
                 config_dict, **kwargs):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._output_q: Queue = output_q
        self._config_dict = config_dict
        self._name = self._config_dict['name']
        self.pulse_count = 0
        self.start_counter = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._config_dict['Pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self._config_dict['Pin'], GPIO.FALLING,
                              callback=lambda x: count_sensor_pulse((self.start_counter, self.pulse_count)))

        Process.__init__(self)
        EdgiseBase.__init__(self, name=self._name, logging_q=logging_q)

        # config = {
        #           "PINNR":int,
        #           "SensorI    bD":int,
        #           "Unit":"cm"
        #           "SensorType":""
        #           }

    def run(self) -> None:
        self.info("Starting Waterflow sensor")

        while not self._stop_event.is_set():
            self.start_counter = 1
            time.sleep(1)
            self.start_counter = 0
            raw_val = self.pulse_count
            flow_s = (raw_val / 396)
            flow_min = (raw_val / 6.6)
            flow_h = (raw_val * 60) / 6.6
            self.pulse_count = 0
            self.info("rawVal: {}".format(raw_val))
            self.info("flowSec: {}".format(flow_s))
            self.info("flowMin: {}".format(flow_min))
            self.info("flowHour: {}".format(flow_h))

            data = {'waterflowSensorData': {
                'rawVal': raw_val,
                'flowSec': flow_s,
                'flowMin': flow_min,
                'flowHour': flow_h
            }}
            measurement = {'data': data}
            self._output_q.put_nowait({'event': json.dumps(measurement)})
            time.sleep(10)
