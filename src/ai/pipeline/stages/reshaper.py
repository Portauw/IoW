import cv2
from src.ai.pipeline.stages import framegrabber as fg
from src.ai.pipeline.stages import PipelineStage
import numpy as np


class Reshaper(PipelineStage):
    """
    Reshaper wil resize incoming frames with new target size
    """

    def __init__(self, target_size=(640, 480), flatten=False, **kwargs):
        """
        Constructor method

        :param target_size: new frame target size, format = (width, height), defaults to (640,480)
        :type target_size: Tuple

        :param flatten: set to True to enable flattening, defaults to False
        :type flatten: bool
        """
        super().__init__(prefix="RES", **kwargs)
        self.target_size = target_size
        self.flatten_bool = flatten

    def __call__(self, input_data, *args, **kwargs):
        """
        Invoke interpreter.
        frame will be resized and flattened, depending on values set in constructor

        :param frame: new incomming frame
        :type frame: np.array
        """
        frame = self.reshape(input_data)
        if self.flatten_bool:
            frame = self.flatten(frame)

        self.next(frame)

    def reshape(self, frame) -> np.array:
        """
        frame will be resized, depending on values set in constructor

        :param frame: new incomming frame
        :type frame: np.array
        """
        frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)
        return frame

    def flatten(self, frame) -> np.array:
        """
        frame will be flattened, depending on values set in constructor

        :param frame: new incomming frame
        :type frame: np.array
        """
        return frame.flatten()

    def __str__(self):
        return f"{super().__str__()}Taget:{self.target_size}, Flatten:{self.flatten_bool}"


##################################
# BELOW CODE IS ONLY FOR TESTING #
##################################
if __name__ == '__main__':

    my_framegrabber = fg.FrameGrabber("video/Edgise-1up-lowres-shifted.mp4")
    my_reshaper = Reshaper((300, 300), False)

    while True:
        ret, frame = my_framegrabber()
        if not ret:
            break
        frame = my_reshaper(frame)

        # Display the resulting frame
        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    my_framegrabber.source.release()
    cv2.destroyAllWindows()
