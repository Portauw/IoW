#!/usr/bin/python3

import os
from src.update import UpdateWatcher
from src.registration import RegisterProcess
from src.uploader import UploaderProcess
from src.edgise_mqtt import EdgiseMQTT
from src.device_state import DeviceState
from src.edgise_logger import EdgiseLogger


from config import cfg
import queue
import time
import sys
from multiprocessing import Queue, Process, Lock
from multiprocessing import Event as mpEvent
from src.base import EdgiseBase
from typing import List
import json


class Handler(EdgiseBase):
    def __init__(self, stop_event: mpEvent, logging_q: Queue, mqtt_send_q):
        self._logging_q = logging_q
        self._stop_event = stop_event
        EdgiseBase.__init__(self, name="MAIN", logging_q=logging_q)
        self.info('Initializing IoW application')

        # queues to sync data between threads
        self._data_q = Queue()
        self._cmd_q_update_watcher = Queue()
        self._cmd_q_main_process = Queue()
        self._mqtt_send_q = mqtt_send_q

        self._services: List = []

        # Initialize registration process
        self.registration_process = RegisterProcess(stop_event=self._stop_event,
                                                    logging_q=self._logging_q)

        self._services.append(self.registration_process)

        # Initialize update watcher
        self.update_watcher = UpdateWatcher(stop_event=self._stop_event,
                                            cmd_q=self._cmd_q_update_watcher,
                                            logging_q=self._logging_q)

        self._services.append(self.update_watcher)

        # Initialze MQTT process
        self.edgise_mqtt = EdgiseMQTT(stop_event=self._stop_event,
                                      data_q=self._data_q,
                                      cmd_qs=[self._cmd_q_update_watcher,
                                              self._cmd_q_main_process],
                                      send_q=self._mqtt_send_q,
                                      logging_q=self._logging_q)

        self._services.append(self.edgise_mqtt)

        # Initialize state process
        self.state_process = DeviceState(stop_event=self._stop_event,
                                         send_q=self._mqtt_send_q,
                                         logging_q=self._logging_q)

        self._services.append(self.state_process)

        # Initialize uploader process
        self.uploader_process = UploaderProcess(stop_event=self._stop_event,
                                                logging_q=self._logging_q)

        self._services.append(self.uploader_process)

        self.info('--------------------------- App initialization complete ---------------------------')

    def stop(self):
        self.info('Stopping services')
        self._stop_event.set()

        for service in self._services:
            service.join()

        self.info("Quitting.")

    def main(self):

        for service in self._services:
            service.start()

        # restart command handler
        while True:
            cmd = ""
            try:
                cmd = self._cmd_q_main_process.get_nowait()
            except queue.Empty:
                pass
            except Exception as e:
                try:
                    self._logging_q.put_nowait(self.error(f"Unknown exception : {e}"))
                except Exception as e:
                    self.info(f"ERROR! {e}")

            if cmd == "RESTART":
                self.stop()
                break

            time.sleep(1)


if __name__ == '__main__':
    with open(
            f"{cfg.root_dir}/Asciiart.iow") as f:  # The with keyword automatically closes the file when you are done
        print(f.read())

    logging_q = Queue()
    stop_event = mpEvent()
    mqtt_send_q = Queue()
    fake_stop = mpEvent()

    # Initialize a logging process that takes an incoming queue
    logging_process = EdgiseLogger(stop_event=fake_stop,  # Just for now
                                   incoming_q=logging_q,
                                   outgoing_q=mqtt_send_q)

    # Directly start logging process
    logging_process.start()

    handler = Handler(stop_event=stop_event,
                      logging_q=logging_q,
                      mqtt_send_q=mqtt_send_q)

    handler.main()

    # fake_stop.set()
    # logging_process.join()

    os.execv(sys.executable, ['python3'] + sys.argv)
