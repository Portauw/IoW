from multiprocessing import Process, Event, Queue, Lock
import time
import numpy as np
from src.base import EdgiseBase
from grove.adc import ADC
from config import cfg
import json


class VibrationSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, input_q: Queue, output_q: Queue, config_dict,
                 resource_lock: Lock, **kwargs):
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
        sample_list = []
        sample_time = time.time() + 60
        # ADC should sample at 100/ 400 kHz according to i2c
        while time.time() < sample_time:
            sample = self.adc.read(self._config_dict['pin'])
            sample_list.append(sample)
        freq = np.amax(np.real(np.fft.fft(sample_list)))
        return freq

    def run(self) -> None:
        self.info("Starting vibration sensor")

        while not self._stop_event.is_set():

            self.i2c_lock.acquire()
            try:
                raw_val = self.read_sensor()
            finally:
                self.i2c_lock.release()
            self.info("Frequency of Vibration: {}".format(raw_val))
            data = {'vibrationSensorData':
                {
                    'freqOfVibration': raw_val
                }
            }
            measurement = {'data': data}
            self._output_q.put_nowait({'event': json.dumps(measurement)})
            time.sleep(10)
