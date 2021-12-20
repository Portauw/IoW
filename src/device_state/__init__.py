import time
from config import cfg
from threading import Thread, Event
from queue import Queue
from typing import Dict, List
import os
import json
from multiprocessing import Queue as mpQueue
from src.base import EdgiseBase


VOLTAGE_ID_LIST: List = ['core', 'sdram_c', 'sdram_i', 'sdram_p']


class StateData:
    temperature: float = 15.0
    voltage: List[str] = ['volt=0.000V', 'volt=0.000V', 'volt=0.000V', 'volt=0.000V']
    ip: str = "unknown"
    memory_usage: List[str] = ['0', '0']
    fps: float = 0.0


class DeviceState(Thread, EdgiseBase):
    def __init__(self, stop_event: Event, send_q: Queue, logging_q: mpQueue, **kwargs):
        self._stop_event = stop_event
        self._send_q = send_q
        self._state = StateData()

        Thread.__init__(self)
        EdgiseBase.__init__(self, name="STATE", logging_q=logging_q)

    def get_ip(self):
        try:
            ip = os.popen('hostname -I').read().split(' ')[0]  # damn that fugly...
            if len(ip) < 5:
                ip = 'no connection'
        except Exception as e:
            self.error(f"[get_ip] Exception : {e}")
            ip = 'unknown'

        return ip

    def get_temperature(self):
        platform = os.uname()
        if platform[1] == "raspberrypi":
            try:
                tmp: str = os.popen("/opt/vc/bin/vcgencmd measure_temp").readline()
                tmp = tmp.split("=")[-1]
                return float(tmp.split("'")[0])
            except Exception as e:
                self.error(f"[get_temperature] {e}")

        else:
            try:
                t: str = os.popen("cat /sys/class/thermal/thermal_zone0/temp ").readline()
                return float(t)/1000.
            except:
                return 15.0

    def get_voltage(self):
        voltage_list = []
        platform = os.uname()
        if platform[1] == "raspberrypi":
            try:
                for _id in VOLTAGE_ID_LIST:
                    voltage_list.append(_id + ":" + str(os.popen(f"vcgencmd measure_volts {_id}").read())[5:-1])
                return voltage_list
            except Exception as e:
                self.error(f"[get_voltage] Error : {e}")
                return ['0', '0', '0', '0']

    def get_memory_usage(self):
        try:
            memory_usage = os.popen('free -t -m').readlines()[-1].split()[1:3]

            return memory_usage
        except Exception as e:
            self.error(f"[get_memory_usage] Error : {e}")
            return ['0', '0']

    def run(self) -> None:
        while not self._stop_event.is_set():

            self._state.temperature = self.get_temperature()
            self._state.memory_usage = self.get_memory_usage()
            self._state.ip = self.get_ip()
            self._state.voltage = self.get_voltage()

            message = json.dumps(self._state.__dict__)

            self._send_q.put({'state': message})

            self._stop_event.wait(timeout=cfg.state_sync_interval)
            # time.sleep(cfg.state_sync_interval)

        self.info("Quitting.")

    @property
    def state(self):
        return self._state
