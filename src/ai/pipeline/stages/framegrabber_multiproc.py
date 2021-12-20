import os
import cv2
import numpy as np
from src.ai.pipeline.stages import PipelineStage
from multiprocessing import Process, Pipe, Queue, Event
import time
import io
import queue
from src.base import EdgiseBase

try:
    import picamera
except:
    pass

try:
    from utils.gstreamer import gstreamer
except:
    pass


class FrameGrabberMulti(PipelineStage, EdgiseBase):
    """
    This block wil grab frames from a specified source
    """

    def __init__(self, stop_event: Event, logging_q: Queue, **kwargs):
        """
        Constructor method

        :param source: path to video source
        :type source: string
        """

        PipelineStage.__init__(self, prefix="FGM", **kwargs)
        EdgiseBase.__init__(self, name="FGM", logging_q=logging_q)

        self._frame_q = Queue()
        self._stop_event = stop_event
        self._logging_q = logging_q

        self._last_frame = np.zeros((300, 300, 3), dtype=np.uint8)

        self._start_getter_process()

        self._error_counter = 0
        self.info("Framegrabber process launched")

    @property
    def last_frame(self) -> np.ndarray:
        return self._last_frame

    @property
    def valid_frame(self):
        return True

    def _detect_coral_dev_board(self) -> bool:
        try:
            if 'MX8MQ' in open('/sys/firmware/devicetree/base/model').read():
                self.info('Detected Edge TPU dev board.')
                return True
        except:
            pass
        return False

    def _detect_raspberry_pi(self) -> bool:
        platform = os.uname()
        try:
            if platform[1] == "raspberrypi" and platform[4].startswith("arm"):
                self.info('Detected Raspberry Pi.')
                return True
            else:
                return False
        except:
            return False

    def _getter_process_factory(self) -> Process:

        proc = None

        if self._detect_coral_dev_board():
            proc = Process(target=self._get_frames_coral_dev, args=(self._frame_q,
                                                                    self._stop_event))
        elif self._detect_raspberry_pi():
            proc = Process(target=self.get_frames, args=(self._frame_q,
                                                         self._stop_event))

        return proc

    def _get_frames_coral_dev(self, q: Queue, stop: Event):

        def callback(img):
            nonlocal q
            img = img[:300, :300, :3]
            try:
                if q.qsize() < 2:
                    q.put_nowait(img)
            except queue.Empty:
                pass

        pipeline = gstreamer.setup_pipeline(callback,
                                          src_size=(640, 480),
                                          appsink_size=(300, 300),
                                          videosrc="/dev/video0",
                                          videofmt="raw")

        pipeline.run()

        while True:
            if stop.is_set():
                break

        q.close()
        self.info(f"Quitting.")

    def _start_getter_process(self):
        self._getter_process = self._getter_process_factory()
        self._getter_process.start()

    def __call__(self, *args, **kwargs) -> np.array:
        """
        return a frame to the next stage
        """

        try:
            self._last_frame = self._frame_q.get(block=True, timeout=0.1)
        except queue.Empty:
            self.info(f"Queue empty")
            self._error_counter += 1
            time.sleep(1)

            if self._error_counter >= 10:
                self._error_counter = 0
                self.error("Queue empty, camera not running, trying a relaunch")
                self.stop_grabber()
                self._start_getter_process()
        else:
            self._error_counter = 0

            self.next(self.last_frame)

    def stop_grabber(self):
        self.clear_pipe()
        self._getter_process.join(timeout=0.5)

    def clear_pipe(self):
        while not self._frame_q.empty():
            try:
                tmp = self._frame_q.get_nowait()
            except queue.Empty:
                self.info("Frame Q empty.")

    def get_frames(self, q: Queue, stop: Event):
        """
        Returns a resized frame from picamera.
        """
        with picamera.PiCamera(resolution=(640, 480), framerate=30) as camera:
            time.sleep(2)

            self.info(f"Camera open.")

            stream = io.BytesIO()
            for _ in camera.capture_continuous(stream,
                                               format='rgba',
                                               use_video_port=True,
                                               resize=(300, 300)):

                stream.truncate()
                stream.seek(0)
                img = np.frombuffer(stream.getvalue(), dtype=np.uint8)
                img = np.reshape(img, (304, 320, 4))
                img = img[:300, :300, :3]
                try:
                    if q.qsize() < 2:
                        q.put_nowait(img)
                except queue.Empty:
                    pass

                if stop.is_set():
                    break

        q.close()
        self.info(f"Quitting.")

    def __str__(self) -> str:
        return f"{super().__str__()} Framegrabber - Raspberry Pi"

    @property
    def getter_process(self):
        return self._getter_process
