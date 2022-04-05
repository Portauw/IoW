import time
from config import cfg
from threading import Thread, Event
import os
import requests
from multiprocessing import Queue
from src.base import EdgiseBase


class UploaderProcess(Thread, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, **kwargs):
        self._stop_event = stop_event
        Thread.__init__(self)
        EdgiseBase.__init__(self, name="UPLOAD", logging_q=logging_q)

    def run(self) -> None:
        while not self._stop_event.is_set():

            # wait for proper manual configuration in platform
            while not cfg.has_device_id:
                time.sleep(cfg.uploader_interval)  # Sleep long enough, a bit of delay on this is not so bad anyway
            while not cfg.has_project_id:
                time.sleep(cfg.uploaderInterval)  # See above

            upload_folder = cfg.upload_folder_absolute_path
            if os.listdir(upload_folder):
                for file in os.listdir(upload_folder):
                    if not file.startswith("."):
                        os.chdir(upload_folder)
                        self.info(f"Uploading file {file}")
                        try:
                            file_to_upload = {'file': (file, open(file, "rb"), 'image/jpeg')}
                            response = requests.post(cfg.file_upload_url, files=file_to_upload)
                            if response and response.status_code == 200:
                                self.info(f"Upload success")
                                os.remove(file)
                        except Exception as e:
                            self.error(f"Error during upload : {e}")

            self._stop_event.wait(timeout=cfg.uploader_interval)
            # time.sleep(cfg.uploader_interval)

        self.info(f"Quitting.")
