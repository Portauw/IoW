import cv2
import numpy as np
from src.ai.pipeline.stages import PipelineStage
from multiprocessing import Queue, Process, Event, Pipe


class FrameGrabber(PipelineStage):
    """
    This block wil grab frames from a specified source
    """

    def __init__(self, source, **kwargs):
        """
        Constructor method

        :param source: path to video source
        :type source: string
        """
        super().__init__(prefix="FG ", **kwargs)

        self._source = source
        self.source = cv2.VideoCapture(self._source)
        self._valid_frame = False
        self._valid_frame, self._last_frame = self.get_frame()

    @property
    def last_frame(self) -> np.ndarray:
        return self._last_frame

    @property
    def valid_frame(self) -> bool:
        return self._valid_frame

    def __call__(self, *args, **kwargs) -> np.array:
        """
        Invoke interpreter
        """

        self.update_frame()
        if self._valid_frame:
            self.next(self.last_frame)
        else:
            print(f"{super().__str__()}Frame invalid, stopping")

    def update_frame(self):
        valid, img = self.get_frame()

        if valid:
            self._last_frame = img
            self._valid_frame = True
        else:
            self._valid_frame = False

    def get_frame(self) -> np.array:
        """
        Returns a frame from source.
        """
        return self.source.read()

    def __str__(self) -> str:
        return f"{super().__str__()}{self.source}"
