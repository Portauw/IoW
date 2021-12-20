from src.ai.pipeline.stages import PipelineStage
from src.ai.objects import CentroidObject, Zone
from typing import List


class ZoneFilter(PipelineStage):
    """
    This will filter object with respect to zones
    """

    def __init__(self, zone_list: List[Zone] = None, keep_inside: bool = True, **kwargs):
        """
        Constructor method of Zone Filter

        :param zone_list: list of the zones
        :type zone_list: List[Zone]

        :param keep_inside: set to True to enable keep the object inside the zones, False to keep the objects outside
        :type keep_inside: bool
        """
        super().__init__(prefix="ZF", **kwargs)
        self._zone_list = zone_list
        self._keep_inside = keep_inside
        self._output = None

    @property
    def keep_inside(self) -> bool:
        return self._keep_inside

    @keep_inside.setter
    def keep_inside(self, keep_inside: bool):
        self._keep_inside = keep_inside

    @property
    def zone_list(self) -> List[Zone]:
        return self._zone_list

    @zone_list.setter
    def zone_list(self, zone_list):
        self._zone_list = zone_list

    def __call__(self, input_data: List[CentroidObject], *args, **kwargs):
        """
        Filter the list of CentroidObject's.

        :param input_data: List of CentroidObject's
        """

        self._output = []

        for obj in input_data:
            keep = False
            for zone in self._zone_list:
                if zone(obj) == self._keep_inside:
                    keep = True

            if keep:
                self._output.append(obj)

        self.next(self._output)

    def __str__(self):
        return f"{super().__str__()}Zone count:{len(self._zone_list)}, Keep inside:{self._keep_inside}"
