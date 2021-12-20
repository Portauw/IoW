import cv2
from src.ai.pipeline.stages import PipelineStage
import numpy as np


class Rotater(PipelineStage):
    """
    Will rotate an image
    """

    def __init__(self, angle: float = -90, **kwargs):
        """
        Constructor method

        :param angle: angle in degree to rotate with -- at this point only -90deg is supported
        """
        super().__init__(prefix="ROT", **kwargs)
        self._angle = angle

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, new_angle: float):
        self._angle = new_angle

    def __call__(self, input_data: np.ndarray, *args, **kwargs):
        """
        will rotate a frame
        """
        if self._angle == -90:
            frame = cv2.rotate(input_data, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            frame = input_data

        self.next(frame)

    def __str__(self):
        return f"{super().__str__()}Angle:{self._angle}"
