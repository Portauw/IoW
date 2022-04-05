from multiprocessing import Process, Event, Queue, Lock
import time
import numpy as np
from src.base import EdgiseBase
from config import cfg
import json


class RandomDataGenerator(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, input_q: Queue, output_q: Queue, config_dict, **kwargs):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._input_q: Queue = input_q
        self._output_q: Queue = output_q
        self._config_dict = config_dict

        Process.__init__(self)
        EdgiseBase.__init__(self, name=self._config_dict['name'], logging_q=logging_q)

    def generate_random_data(self):
        pass

    def run(self) -> None:
        self.info("Starting data generator")

        while not self._stop_event.is_set():
            self.info("Frequency of Vibration: {}".format(raw_val))
            data = {'vibrationSensorData':
                {
                    'freqOfVibration': raw_val
                }
            }
            measurement = {'data': data}
            self._output_q.put_nowait({'event': json.dumps(measurement)})
            time.sleep(10)
