import time
from config import cfg
import base_config
# from src.database import DbManager
# from threading import Thread
from src.ai.pipeline import Pipeline
from src.ai.pipeline.stages import FrameGrabber, Reshaper, ImagePreprocessor, AiEngine, ShitTracker, ShitTracker2, SchmittTrigger
from src.ai.objects import zone as zn
from src.ai.objects import Zone
import queue
import cv2
from multiprocessing import Queue, Event, Process
from threading import Thread
from src.base import EdgiseBase
import json
from src.ai.pipeline.stages import FrameGrabberMulti


class CountData:
    entered: bool = True
    timestamp: int = 0


def create_zone_from_dict(zone_dict) -> Zone:
    zn = Zone((zone_dict['area']['point1']['x'], zone_dict['area']['point1']['y']),
              (zone_dict['area']['point2']['x'], zone_dict['area']['point2']['y']),
              bool(zone_dict['edgeZone']))

    return zn


def initialize_schmitt_trigger():
    zones_dict = cfg.zones
    zones_list = [create_zone_from_dict(zone) for zone in zones_dict]
    return SchmittTrigger(zones_list)


UPDATE_INTERVAL = 2


class VideoProcessor(Thread, EdgiseBase):
    def __init__(self,
                 stop_event: Event,
                 data_q: Queue,
                 cmd_q: Queue,
                 logging_q: Queue,
                 mqtt_send_q: Queue,
                 testing: bool = False,
                 testing_video_file_path: str = None):

        Thread.__init__(self)
        EdgiseBase.__init__(self, name="VIDPROC", logging_q=logging_q)

        self._stop_event = stop_event
        self._data_q = data_q
        self._cmd_q = cmd_q
        self._mqtt_send_q = mqtt_send_q
        self._logging_q = logging_q
        self._fps: float = 0.0

        src = 0
        if testing:
            src = testing_video_file_path

        # self.frame_grabber = FrameGrabber(src)
        self.frame_grabber = FrameGrabberMulti(stop_event, self._logging_q)
        # self.reshaper = Reshaper((300, 300), flatten=False)
        # self.preprocessor = ImagePreprocessor(method='bgr2rgb')
        self.engine = AiEngine(cfg.ai_model_absolute_path, class_list=[0])
        self.tracker = ShitTracker2()
        self.schmitt_trigger = initialize_schmitt_trigger()

        self.pipeline = self._initialize_pipeline()

    def run(self) -> None:

        start_time, sync_time, fps_acc = time.time(), time.time(), [30, 1]
        c = 0

        self._data_q.put({'version_text': "1.0 - Live"})

        while not self._stop_event.is_set():

            try:
                cmd = self._cmd_q.get_nowait()
            except queue.Empty:
                cmd = ""
                pass

            if cmd == "UPLOAD":
                last_frame = self.frame_grabber.last_frame
                last_frame = last_frame[..., ::-1]
                cv2.imwrite(f'{cfg.upload_folder_absolute_path}/last_frame.jpg', img=last_frame)
                self.info(f"Copied image to {cfg.upload_folder_absolute_path}/last_frame.jpg -- ready to upload!")

            # This calls the actual video processing pipeline!
            self.pipeline()

            if self.frame_grabber.valid_frame:
                # Detect people moving in and out
                output = self.schmitt_trigger.output

                if len(output) > 0:
                    for movement in output:
                        if movement[1][-1] == 2:  # Person entered
                            newdata = CountData()
                            newdata.entered = True
                            newdata.timestamp = int(time.time())
                            self._mqtt_send_q.put({'event': json.dumps(newdata.__dict__)})
                            self._data_q.put({'incr_in': 1, 'incr_estimated': 1})
                            self.info('Person entered')
                        elif movement[1][-1] == 0:  # Person left
                            newdata = CountData()
                            newdata.entered = False
                            newdata.timestamp = int(time.time())
                            self._mqtt_send_q.put({'event': json.dumps(newdata.__dict__)})
                            self._data_q.put({'incr_out': 1, 'decr_estimated': 1})
                            self.info('Person left')

            # Calculate FPS  (Accumulate, calculate later)
            c += 1

            # Write data to database
            if time.time() - sync_time > UPDATE_INTERVAL:
                fps = int(float(c) / float(UPDATE_INTERVAL))
                c = 0
                self._fps = fps
                self._data_q.put({'fps': self._fps})
                sync_time = time.time()

        self._data_q.put({'version_text': "1.0"})
        self.frame_grabber.clear_pipe()
        self.info("Framegrabber pipe cleared")
        # self.frame_grabber.getter_process.join(timeout=0.2)
        self.frame_grabber.stop_grabber()
        # self.frame_grabber.getter_process.terminate()
        self.info(f"Quitting.")

    def _initialize_pipeline(self):
        """ Initialize pipeline for each frame"""
        pipeline_stages = []

        pipeline_stages.append(self.frame_grabber)
        # pipeline_stages.append(self.reshaper)
        # pipeline_stages.append(self.preprocessor)
        pipeline_stages.append(self.engine)
        pipeline_stages.append(self.tracker)
        pipeline_stages.append(self.schmitt_trigger)

        return Pipeline(stages=pipeline_stages)

    @property
    def fps(self):
        return self._fps
