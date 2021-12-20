from typing import Tuple, List
import numpy as np


class CentroidObject:
    """
    Object with label, score, centroid, size and bounding box
    """

    def __init__(self,
                 label: int = 0,
                 centroid: Tuple[float, float] = (0, 0),
                 size: Tuple[float, float] = (0, 0),
                 score: float = 0.0,
                 bbox: np.array = None,
                 **kwargs):
        """
        Constructor method  -- at this point bbox overwrites centroid and size

        :param label: label, defaults to 0
        :type label: int

        :param centroid: relative coordinates of centroid, defaults to (0, 0)
        :type centroid: Tuple[float, float]

        :param size: relative size of bounding box, defaults to (0, 0)
        :type size: Tuple[float, float]

        :param score: detection score
        :type score: float

        :param bbox: bounding box array (from tflite ssd postprocessing)
        :type bbox: np.array

        :param args: Ignored
        """

        if bbox is not None:

            self.from_tflite_postprocessed_ssd_tensor(box=bbox, label=label, score=score)

        else:
            self._bbox = [(0.0, 0.0), (0.0, 0.0)]
            self._label = label
            self._centroid = centroid
            self._size = size
            self._score = score
            self._update_bbox()

    def _update_bbox(self):
        """ Updates the bounding box from the size and centroid """
        self._bbox = [(self.centroid[0] - self._size[0] / 2.0, self.centroid[1] - self._size[1] / 2.0),
                      (self.centroid[0] + self._size[0] / 2.0, self.centroid[1] + self._size[1] / 2.0)]

    def _update_centroid_size(self):
        """ Updates the centroid and size from the bounding box """
        xmin = self._bbox[0][0]
        ymin = self._bbox[0][1]
        xmax = self._bbox[1][0]
        ymax = self._bbox[1][1]

        w = (xmax - xmin)
        h = (ymax - ymin)

        center_x = w / 2.0 + xmin
        center_y = h / 2.0 + ymin

        self._size = (w, h)
        self._centroid = (center_x, center_y)

    def from_tflite_postprocessed_ssd_tensor(self, box: np.array, label: int, score: float):
        """

        just some info about the tflite postprocess output :

            TFLite_Detection_PostProcess custom op node has four outputs:
            detection_boxes: a float32 tensor of shape [1, num_boxes, 4] with box
            locations
            detection_classes: a float32 tensor of shape [1, num_boxes]
            with class indices
            detection_scores: a float32 tensor of shape [1, num_boxes]
            with class scores
            num_boxes: a float32 tensor of size 1 containing the number of detected
            boxes
        """

        self.label = label
        self.score = score
        self.bbox = [(box[1], box[0]), (box[3], box[2])]
        self._update_centroid_size()

    def get_center_x(self) -> float:
        """
        Get relative X coordinate of centroid
        """
        return self._centroid[0]

    def get_center_y(self) -> float:
        """
        Get relative Y coordinate of centroid
        """
        return self._centroid[1]

    def get_centroid(self) -> Tuple[float, float]:
        """
        Get the centroid as tuple
        :return: Tuple[float, float]
        """
        return self._centroid

    @property
    def label(self) -> int:
        return self._label

    @label.setter
    def label(self, new_label: int):
        """
        set a new label
        :param new_label: new label id
        :return: None
        """
        self._label = new_label

    @property
    def score(self) -> float:
        """
        get score
        :return: score as float
        """
        return self._score

    @score.setter
    def score(self, new_score: float):
        """
        Set a new score
        :param new_score: new score as float
        :return: None
        """
        self._score = new_score

    @property
    def centroid(self):
        return self._centroid

    @centroid.setter
    def centroid(self, new_centroid: Tuple[float, float]):
        """
        Sets the centroid of the object, and translates the current bounding box to this position

        :param new_centroid: new centroid
        :return: None
        """
        self._centroid = new_centroid
        self._update_bbox()

    def set_centroid(self, centroid: Tuple[float, float]):
        """
        Deprecated -- use property instead

        :param centroid: new centroid
        :return: None
        """
        self.centroid = centroid

    @property
    def size(self) -> Tuple[float, float]:
        """
        Get the size as Tuple
        :return: Size as Tuple
        """
        return self._size

    @size.setter
    def size(self, new_size):
        """
        Get the size as Tuple
        :return: Size as Tuple
        """
        self._size = new_size
        self._update_bbox()

    def set_size(self, size: Tuple[float, float]):
        """
        Sets the size of the object, and creates new bounding box around its centroid

        :param size: new size
        :return: None
        """
        self.size = size

    def get_abs_centroid(self, frame_size: Tuple[int, int]) -> Tuple[int, int]:
        """
        Get the absolute centroid in accordance to the frame size

        :param frame_size: Size of image to cast the centroid onto
        :return: Absolute centroid
        """
        return int(frame_size[0] * self._centroid[0]), int(frame_size[1] * self._centroid[1])

    def get_width(self) -> float:
        """
        Get relative width
        """
        return self._size[0]

    def get_height(self) -> float:
        """
        Get relative height
        """
        return self._size[1]

    def get_p1(self) -> Tuple[float, float]:
        """
        Get p1 of bounding box
        """
        return self._bbox[0]

    def get_p2(self) -> Tuple[float, float]:
        """
        Get p2 of bounding box
        """
        return self._bbox[1]

    @property
    def bbox(self) -> List[Tuple[float, float]]:
        """
        Get the bounding box p1 and p2
        :return: bounding box with p1 as [0] and p2 as [1]
        """
        return self._bbox

    @bbox.setter
    def bbox(self, new_bbox: List[Tuple[float, float]]):
        """
        Set the bounding box p1 and p2
        :param new_bbox: bounding box with p1 as [0] and p2 as [1]
        """
        self._bbox = new_bbox
        self._update_centroid_size()

    def get_bbox(self) -> List[Tuple[float, float]]:
        """
        Get the bounding box p1 and p2
        :return: bounding box with p1 as [0] and p2 as [1]
        """
        return self._bbox

    def get_abs_bbox(self, frame_size: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Get the bounding box absolute values according to the frame size
        :param frame_size: frame size in px (int)
        :return: p1 and p2 of bounding box absolute values
        """
        return [(int(self._bbox[0][0] * frame_size[0]), int(self._bbox[0][1] * frame_size[1])),
                (int(self._bbox[1][0] * frame_size[0]), int(self._bbox[1][1] * frame_size[1]))]

    def get_abs_p1(self, frame_size: Tuple[int, int]) -> Tuple[float, float]:
        """
        Get absolute p1 of bounding box
        """
        return int(self._bbox[0][0] * frame_size[0]), int(self._bbox[0][1] * frame_size[1])

    def get_abs_p2(self, frame_size: Tuple[int, int]) -> Tuple[float, float]:
        """
        Get absolute p2 of bounding box
        """
        return int(self._bbox[1][0] * frame_size[0]), int(self._bbox[1][1] * frame_size[1])

    def __str__(self) -> str:
        """
        Returns human readable string
        """
        return f"CentroidObject: {self._label: .0f} @ (x:{self._centroid[0]:.2f}, y:{self._centroid[1]:.2f}), (w:{self._size[0]:.2f}, h{self._size[1]:.2f})"
