from src.ai.objects import CentroidObject
from typing import Tuple, List
import math
import numpy as np


class TrackedObject:
    """
    Add's an ID and speed vector to the CentroidObject Class
    """

    def __init__(self,
                 ID: int = -1,
                 velocity: Tuple[float, float] = (0, 0),
                 bbox_velocity: List[Tuple[float, float]] = None,
                 centroid_object: CentroidObject = None,
                 **kwargs):
        """
        bbox_velocity overwrites velocity
        :param ID: ID of the object
        :param velocity: Speed vector [0..1]
        :param bbox_velocity: Velocity of bounding box points [p1, p2]
        """

        if bbox_velocity is None:
            self.velocity = velocity
        else:
            self.bbox_velocity = bbox_velocity

        self._id = ID
        self._centroid_object = centroid_object

    @property
    def velocity_vector(self) -> Tuple[float, float]:
        """
        get velocity vector as tuple
        :return: Tuple[float, float]
        """
        return self._velocity

    @property
    def velocity(self) -> float:
        """
        Get vector magnitude
        :return: Magnitude as float
        """
        return math.sqrt(math.pow(self._velocity[0], 2) + math.pow(self._velocity[1], 2))

    @velocity.setter
    def velocity(self, velocity):
        """
        Set velocity, bbox_velocity will be set to the same for both points
        :param velocity: Tuple[float, float]
        :return: None
        """
        self._velocity = velocity
        self._bbox_velocity = [velocity, velocity]

    @property
    def ID(self) -> int:
        """
        Get ID
        :return: ID as int
        """
        return self._id

    @property
    def centroid_object(self) -> CentroidObject:
        """
        Get CentroidObject
        :return: CentroidObject
        """
        return self._centroid_object

    @property
    def bbox_velocity(self) -> List[Tuple[float, float]]:
        """
        Get bbox velocity
        :return: bbox veloicty as [p1_velocity, p2_velocity]
        """
        return self._bbox_velocity

    @bbox_velocity.setter
    def bbox_velocity(self, bbox_velocity):
        """
        Set the bbox velocity as List[Tuple[float, float]]
        :param bbox_velocity:
        :return:
        """
        self._bbox_velocity = bbox_velocity
        self.velocity = tuple(np.mean(self.bbox_velocity, axis=0))

    def __str__(self):
        return f"TrackedObject {self._id} @ {self._centroid_object.centroid} : v={self.velocity}"
