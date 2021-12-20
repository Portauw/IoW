from src.ai.pipeline.stages import PipelineStage
from typing import List, Dict, Tuple
from src.ai.objects import CentroidObject, TrackedObject
from scipy.spatial.distance import sqeuclidean


class ShitTracker(PipelineStage):
    """
    Shitty implementation of CentroidTracker

    N^2 complexity, and matches every object to the first that is close enough -- no sorting!
    """

    def __init__(self, max_dist: float = 0.01, frame_loss_max: int = 10, filter_value: float = 0.2, **kwargs):
        """
        Initializer of a shitty class
        :param max_dist: max jump
        :param frame_loss_max: max continuous frames that object can be dissapeared
        """
        super().__init__(prefix="ST", **kwargs)
        self._max_distance: float = max_dist  # Max jump
        self._max_frame_loss: int = frame_loss_max  # max frame loss
        self._dissapeared_objs: Dict[int, int] = {}  # counters for frame loss
        self._tracking_table: List[TrackedObject] = []  # tracking table dict holding ID and CentroidObject
        self._movement_vects: Dict[int, Tuple[float, float]] = {}  # movement vectors
        self._next_id: List[int] = [0]  # next ID to use
        self._filter_value = filter_value

    def __call__(self, input_data: List[CentroidObject], *args, **kwargs):
        obj_to_deregister = []
        new_objs: List[CentroidObject] = input_data

        for obj in self._tracking_table:

            min_dist = self._max_distance  # make min dist the max jump
            matched_obj = None  # placeholder for the matched obj

            for new_obj in new_objs:
                if new_obj.label == obj.centroid_object.label:
                    if self._dist(obj.centroid_object, new_obj) < min_dist:
                        matched_obj = new_obj
                    # else:
                    #     print("Distance too big")

            # did we find a good match?
            if matched_obj is not None:
                #
                new_centroid_x = matched_obj.centroid[0] * self._filter_value + \
                                 obj.centroid_object.centroid[0] * (1 - self._filter_value)
                new_centroid_y = matched_obj.centroid[1] * self._filter_value + \
                                 obj.centroid_object.centroid[1] * (1 - self._filter_value)
                obj.centroid_object.centroid = (new_centroid_x, new_centroid_y)
                obj.centroid_object.size = matched_obj.size

                # self._tracking_table[ID] = matched_obj
                new_objs.remove(matched_obj)  # remove from the new list
            else:
                self._dissapeared_objs[obj.ID] = self._dissapeared_objs[obj.ID] + 1
                if self._dissapeared_objs[obj.ID] >= self._max_frame_loss:
                    obj_to_deregister.append(obj)

        for obj in obj_to_deregister:
            self._deregister_obj(obj)

        for obj in new_objs:
            self._register_obj(obj)

        self.next(self._tracking_table)

    @property
    def tracking_table(self) -> List[TrackedObject]:
        return self._tracking_table

    @staticmethod
    def _dist(a: CentroidObject, b: CentroidObject) -> float:
        """
        Distance function for the ShitTracker
        :param a: Centroid Object A
        :param b: Centroid Object B
        :return: distance in float
        """
        dist = sqeuclidean(list(a.centroid), list(b.centroid))
        # print(dist)
        return dist

    def _move_obj(self, index: int, new_obj: CentroidObject):
        """
        Use this to move the known object to the new position
        TODO: implement the fuck out of this
        :param index: index in tracking table of object to move
        :param new_obj: object to move to
        :return: None
        """
        pass

    def _deregister_obj(self, obj: TrackedObject):
        """
        Use this to deregister an ID
        :param obj: Object to remove
        :return: None
        """
        self._tracking_table.remove(obj)
        del self._dissapeared_objs[obj.ID]
        # re-use ID's, but insert them in the front of the list, so that the last one is always the highest
        # Voorlopig uitgeschakeld, omdat hij natuurlijk lijkt te springen omdat de ID gelijk blijft
        # self._next_id.insert(0, index)

    def _register_obj(self, obj: CentroidObject):
        index = self._next_id.pop(0)  # pop the first available ID
        new_obj = TrackedObject(index, velocity=(0., 0.), centroid_object=obj)
        self._tracking_table.append(new_obj)  # add the new object with it's ID to the dict
        self._dissapeared_objs[index] = 0  # add to the dissapeared list
        if len(self._next_id) == 0:  # if there is no new ID available, make the next one available
            # last ID in the line should always be the highest we had yet, so the next one is always free
            self._next_id.append(index + 1)

    def __str__(self) -> str:
        return f"{super().__str__()}MD : {self._max_distance}; MFL : {self._max_frame_loss}"
