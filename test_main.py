import os
from threading import Event
from src.log import logger
from src.update import UpdateWatcher
# from src.ai import VideoProcessor
from src.web_sync import WebUpdater
from src.platform_sync import PlatformProcess
from src.registration import RegisterProcess
from src.display_sync import DisplayUpdater
from src.cleanup import DataBaseCleaner
from config import cfg
import queue
from src.edgise_mqtt import EdgiseMQTT
from src.uploader import UploaderProcess
from src.device_state import DeviceState

from multiprocessing import Queue
from multiprocessing import Event as mpEvent
from src.edgise_logger import EdgiseLogger


class Handler:
    def __init__(self):
        logger.info('[MAIN] Initializing application')
        self._stop_event = Event()
        self._stop_event_2 = mpEvent()

        # queues to sync data between threads
        self._data_q = queue.Queue()
        self._cmd_q_video_processor = queue.Queue()
        self._cmd_q_update_watcher = queue.Queue()
        self._cmd_q_main_process = queue.Queue()
        self._mqtt_send_q = queue.Queue()

        self._logging_q = Queue()

        # Initialize a logging process that takes an incoming queue
        self._logging_process = EdgiseLogger(self._stop_event_2, self._logging_q)

        # Directly start logging process
        self._logging_process.start()

        self._logging_q.put({cfg.logging_info: ["MAIN", "Logging started"]})

        # Initialize registration process
        self.registration_process = RegisterProcess(self._stop_event, logging_q=self._logging_q)

        # Initialize update watcher
        # self.update_watcher = UpdateWatcher(self._stop_event)

        # Initialize AI
        # self.video_processor = VideoProcessor(self._stop_event,
        #                                       data_q=self._data_q,
        #                                       cmd_q=self._cmd_q_video_processor,
        #                                       logging_q=self._logging_q,
        #                                       testing=True,
        #                                       testing_video_file_path="/Users/michael/Documents/Edgise/Projects/2020/telly/mensen_tellen_demo_jef/video/passage_test2_20fps.mp4")
                                              # testing_video_file_path="/Users/sam/Dropbox (Raccoons)/Projecten/Edgise/Telly/media/testing/passage_test2_20fps.mp4")

        # Initialize Display sync
        # self.display_updater = DisplayUpdater(self._stop_event, self._data_q)

        # Initialize Web sync
        # self.web_updater = WebUpdater(self._stop_event)

        # Initialze MQTT connect process
        #self.platform_sync = PlatformProcess(stop_event=self._stop_event, data_q=self._data_q, cmd_q=self._cmd_q)
        self._edgise_mqtt = EdgiseMQTT(self._stop_event,
                                       self._data_q,
                                       [self._cmd_q_video_processor],
                                       self._mqtt_send_q)

        # Initialize Web sync
        # self.web_updater = WebUpdater(self._stop_event)

        # Initialize state process
        self.state_process = DeviceState(self._stop_event, self._mqtt_send_q)

        # Initialize DB cleanup process
        self.database_cleaner = DataBaseCleaner(self._stop_event, interval=60)

        # Initialize uploader process
        self.uploader_process = UploaderProcess(self._stop_event)

        self._logging_q.put_nowait({cfg.logging_info: ["MAIN", f"App init complete"]})

    def main(self):

        platform = os.uname()
        self._logging_q.put_nowait({cfg.logging_info: ["MAIN", f"Platform : {platform}"]})

        # Start registration process
        self.registration_process.start()

        # Start update watcher
        # self.update_watcher.start()

        # Start video processor
        self.video_processor.start()

        # Start web sync
        # self.web_updater.start()

        # Start platform syncing process
        # self.platform_sync.start()
        self._edgise_mqtt.start()

        # Start display sync
        # self.display_updater.start()

        # Start DB Cleaner
        # self.database_cleaner.start()

        # Start uploader process
        self.uploader_process.start()

        # Start state process
        self.state_process.start()

    def stop(self):
        self._logging_q.put_nowait({cfg.logging_info: ["MAIN", f"Quitting application"]})
        self._stop_event.set()


if __name__ == '__main__':
    handler = Handler()
    handler.main()
