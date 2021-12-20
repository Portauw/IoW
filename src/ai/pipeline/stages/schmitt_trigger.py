from typing import List, Dict
from src.ai.objects import TrackedObject
from src.ai.objects.zone import Zone
from src.ai.pipeline.stages import PipelineStage


class SchmittTrigger(PipelineStage):
    """
    Schmitt trigger that checks which zones a centroid has passed.
    Based on the zones it has passed, it will count and deregister the centroid.
    """

    def __init__(self, zones: List[Zone], **kwargs):
        """
        Constructor method

        :param zones: list of zones
        :type zones: list[Zone]
        """
        super().__init__(prefix="SCH", **kwargs)

        self._zones = zones  # list of all zones. Zones[zone number]
        self._zones_visited = {}  # nested dict. Zones_visited[ID][zones]
        self._been_in_edge = {}
        self._output = []

    def __call__(self, input_data, *args, **kwargs):
        """
        Check in which zone a centroid is situated

        :param input_data: list of centroid objects
        :type input_data: CentroidObjects[CentroidObject]
        """

        self._output = []
        self._object_movement(input_data)
        self.next(self._output)

    @property
    def output(self) -> List:
        return self._output

    @property
    def zones(self) -> List[Zone]:
        return self._zones

    def _object_movement(self, objects: List[TrackedObject]) -> None:
        """
        Check object movements in respect to the Zones, creates output if needed

        :param objects: list of centroids to check
        """

        for obj in objects:

            for index, zone in enumerate(self._zones):

                if zone(obj.centroid_object):
                    if zone.edge_zone:
                        if obj.ID not in self._zones_visited:
                            self._zones_visited[obj.ID] = [self._zones.index(zone)]
                        elif index not in self._zones_visited[obj.ID]:
                            self._zones_visited[obj.ID].append(index)
                            self._output.append([int(obj.centroid_object.label), self._zones_visited.pop(obj.ID)])
                    else:
                        if obj.ID in self._zones_visited:
                            if index not in self._zones_visited[obj.ID]:
                                self._zones_visited[obj.ID].append(index)
                    break

    def __str__(self) -> str:
        """
        Returns human readable string
        """
        return f"{super().__str__()}#zones: {len(self._zones)}"
