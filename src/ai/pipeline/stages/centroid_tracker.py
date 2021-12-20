import numpy as np
from typing import List, Dict
from src.ai.objects.centroid_object import CentroidObject
from src.ai.pipeline.stages import PipelineStage
from sklearn.metrics import pairwise_distances_argmin
from collections import defaultdict


class CentroidTracker(PipelineStage):
    """
    This class will track the centroids of detected objects
    """
    def __init__(self, frame_loss_max: int = 10, tracked_centroids: Dict[int, CentroidObject] = None, **kwargs):
        """
        Constructor

        :param frame_loss_max: defines the maximum consecutive frames in which an object can't be matched
        :type frame_loss_max: int

        :param: tracked_centroids: this is a dictionary containing an object id as key and a centroid object as value
        :type tracked_centroids: Dict[int, CentroidObject]
        """
        super().__init__(prefix="CT", **kwargs)
        self.frame_loss_max: int = frame_loss_max
        self.tracked_centroids: Dict[int, CentroidObject] = tracked_centroids
        self.disappeared: Dict[int, int] = defaultdict(int)
        self.object_id = 0

    def __call__(self, input_data: List[CentroidObject], *args, **kwargs):
        """
        invoke interpreter
        :param input_data: list of newly detected centroidobjects
        :return: updated tracking table
        """

        # no data and nothing registered yet -> return empty dict
        if not input_data and not self.tracked_centroids:
            pass
            # return self.tracked_centroids
        # if we have input and if we are not tracking centroids -> register the new centroids
        elif input_data and not self.tracked_centroids:
            # initialize tracking table
            self._register_centroids(input_data)
            # return self.tracked_centroids
        else:
            self.update_tracker(input_data)
            # return self.tracked_centroids

        self.next(self.tracked_centroids)

    @property
    def tracking_table(self) -> Dict[int, CentroidObject]:
        return self.tracked_centroids

    def __str__(self):
        return "CT"

    def update_tracker(self, new_centroid_objects: List[CentroidObject]) -> Dict[int, CentroidObject]:
        """
        updates the current tracking table by matching old centroids with new input data.

        TODO: Max jump en class dependant zijn echt wel nodig

        :param new_centroid_objects: list of newly detected centroidobjects
        :return: updated tracking table
        """
        # create list for old and new centroids as follows
        # [[x1,y1], [x2,y2], ...]
        # the old_centroids list respects the order of the object ids
        old_centroids = [list(v.centroid) for k, v in sorted(self.tracked_centroids.items())]
        # created nested list with new centroids
        new_centroids = [list(centroids._centroid) for centroids in new_centroid_objects]

        # no new data, but there is a tracking table -> all centroids disappear
        if not new_centroids:
            for disappear_centroid_id in list(self.tracked_centroids.keys()):
                self.disappeared[disappear_centroid_id] += 1
                # check if there are centroids that need to be deregistered
                self._deregister_centroids(disappear_centroid_id)
            return self.tracked_centroids

        # if there are more tracked centroids then input -> unused centroids need to increment disappeareed
        if len(old_centroids) >= len(new_centroids):
            matched_centroid_idx_list = self.match_centroids(new_centroids, old_centroids)
            # update the old centroids with the newly matched centroids
            for idx, centroid_id in enumerate(matched_centroid_idx_list):
                # update the tracked_centroids accordingly
                key = list(self.tracked_centroids)[centroid_id]  # TODO: Is via dict key niet ok?
                self.tracked_centroids[key] = new_centroid_objects[idx]
                self.disappeared[key] = 0
            # we now have to filter out the unmatched centroids
            # using a set difference.
            unmatched_centroids = list(set(self.tracked_centroids.keys()) - set(matched_centroid_idx_list))
            # increment self.disappeared for these centroids
            for disappear_centroid_id in unmatched_centroids:
                self.disappeared[disappear_centroid_id] += 1
                self._deregister_centroids(disappear_centroid_id)
        # There are more input then tracked centroids -> register unused centroids
        else:
            matched_centroid_idx_list = self.match_centroids(old_centroids, new_centroids)
            for idx, centroid_id in enumerate(matched_centroid_idx_list):
                key = list(self.tracked_centroids)[idx]
                self.tracked_centroids[key] = new_centroid_objects[centroid_id]
                self.disappeared[key] = 0

            # this is pops all indices from the matched_centroid_idx_list
            # apparently there is no cleaner way to do this
            # thanks python
            # but found the bug
            new_centroid_objects = [i for j, i in enumerate(new_centroid_objects) if j not in matched_centroid_idx_list]
            # register the remaining centroid objects
            self._register_centroids(new_centroid_objects)
        return self.tracked_centroids

    def _register_centroids(self, new_centroids: List[CentroidObject]) -> None:
        """
        Register new centroids into the tracking table

        :param new_centroids: new centroids to register
        :return:
        """
        for new_centroid in new_centroids:
            # keep track of the entire object ?
            self.tracked_centroids[self.object_id] = new_centroid
            self.disappeared[self.object_id] = 0
            # increment ids for now
            self.object_id += 1
        return None

    def _deregister_centroids(self, del_centroid_ids: int) -> None:
        """
        Deregister centroids from the tracking table

        :param del_centroid_ids: ids of centroids to delete from the table
        :return:
        """
        if self.disappeared[del_centroid_ids] > self.frame_loss_max:
            del self.tracked_centroids[del_centroid_ids]
            del self.disappeared[del_centroid_ids]
        return None

    def match_centroids(self, shortest_centroids_list: List[List], longest_centroids_list: List[List]) -> np.ndarray:
        """

        :param shortest_centroids_list: list that will be uniquely mapped on the longest list
        :param longest_centroids_list:
        :return: array where the index corresponds to element from the shortest list
        and the value corresponds to idx of the longest list
        """
        # find the minimum distance in each row and sort the indices based on this minimum value
        # sorting the rows allows us to find which input centroid is closest to our current centroid

        # returns the indices of the closest centroid in the new_centroids list and take the first element
        #  so we cn use this idx

        # X is de korste list van centroids
        # Y is de langste list van centroids
        # de kortste list krijgt altijd een assignement van values
        matched_centroid_indices = pairwise_distances_argmin(shortest_centroids_list, longest_centroids_list,
                                                             metric='euclidean')
        # returns a list, in this list the index of the element is the old centroid and
        # the value is the index of the corresponding element from the list new_centroid_coordinates
        return matched_centroid_indices
