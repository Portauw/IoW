import requests
from config import cfg
from getmac import get_mac_address
from threading import Thread, Event
import time
import json
from src.log import logger
from multiprocessing import Queue
from src.base import EdgiseBase


class RegisterProcess(Thread, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, interval: float = 5, **kwargs):
        self._stop_event = stop_event
        self._interval = interval
        self._mac_address = str(get_mac_address())

        Thread.__init__(self, **kwargs)
        EdgiseBase.__init__(self, name="REG", logging_q=logging_q, **kwargs)

    def run(self) -> None:
        while not self._stop_event.is_set():

            if cfg.has_device_id:
                # logger.info("[REG] Already registered")
                self.info("Already registered")
                break

            try:
                resp = requests.post(cfg.registration_url, json={'macAddress': self._mac_address})
                resp_dict = json.loads(resp.text)

                device_id = resp_dict['deviceId']
                certificate = resp_dict['certificate']
                root_certificate = resp_dict['rootCertificate']
                private_key = resp_dict['privateKey']

                # logger.info(f"Device ID : {device_id}")
                self.info(f"Device ID : {device_id}")
                # logger.info(f"Certificate : {certificate}")
                self.info(f"Certificate : {certificate}")
                # logger.info(f"Root Certificate : {root_certificate}")
                self.info(f"Root Certificate : {root_certificate}")
                # logger.info(f"Private Key : {private_key}")
                self.info(f"Private Key : {private_key}")

                cfg.update_config_with_dict({"deviceId": device_id})

                with open(cfg.mqtt_crt_absolute_path, 'w+') as f:
                    f.write(certificate)

                with open(cfg.mqtt_key_absolute_path, 'w+') as f:
                    f.write(private_key)

                with open(cfg.mqtt_root_pem_absolute_path, 'w+') as f:
                    f.write(root_certificate)

            except Exception as e:
                # logger.error(f"[REG] Can't register yet due to exception {e}")
                self.info(f"Can't register yet due to exception {e}")

            time.sleep(self._interval)

        # logger.info("[REG] stopping thread")
        self.info("Quitting.")
