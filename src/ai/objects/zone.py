from typing import Tuple
from src.ai.objects import CentroidObject


class Zone:
    """
    Defines a zone in an image
    """

    def __init__(self, p1: Tuple[float, float], p2: Tuple[float, float], edge_zone: bool):
        """
        Constructor method
        :param edge_zone: if a zone is an edge zone
        :param p1: top left point of zone
        :type p1: Tuple[float, float]
        :param p2: bottom right point of zone
        :type p2: Tuple[float, float]
        """
        self.edge_zone = edge_zone
        self.p1 = p1
        self.p2 = p2

    def __call__(self, input_data: CentroidObject, *args, **kwargs) -> bool:
        """
        Returns True if input_data is inside the zone

        :param input_data: CentroidObject which contains the point to check
        :type input_data: CentroidObject
        :param args: Ignored
        :param kwargs: Ignored
        """
        if self.p1[0] < input_data.get_center_x() < self.p2[0] and \
                self.p1[1] < input_data.get_center_y() < self.p2[1]:
            return True
        else:
            return False

    def __str__(self) -> str:
        """
        Readable print
        """
        return f"box : \np1({self.p1[0]}, {self.p1[1]})\np2({self.p2[0]}, {self.p2[1]})\n"
