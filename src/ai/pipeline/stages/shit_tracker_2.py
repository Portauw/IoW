from src.ai.pipeline.stages import PipelineStage
from typing import List, Dict, Tuple
from src.ai.objects import CentroidObject, TrackedObject
from scipy.spatial.distance import sqeuclidean, euclidean, seuclidean, braycurtis
import numpy as np
from math import sqrt


class ShitTracker2(PipelineStage):
    """
    Still shitty though...
    """

    def __init__(self,
                 max_score: float = 0.9,
                 frame_loss_max: int = 30,
                 filter_value: float = 0.5,
                 distance_multiplier: float = 2,
                 velocity_multiplier: float = 3,
                 velocity_decay_multiplier: float = 1.0,
                 **kwargs):
        """
        Initializer of a shitty class
        :param max_dist: max jump
        :param frame_loss_max: max continuous frames that object can be dissapeared
        """
        super().__init__(prefix="ST", **kwargs)
        self._max_score: float = max_score  # Max jump
        self._max_frame_loss: int = frame_loss_max  # max frame loss
        self._dissapeared_objs: Dict[int, int] = {}  # counters for frame loss
        self._tracking_table: List[TrackedObject] = []  # tracking table dict holding ID and CentroidObject
        self._movement_vects: Dict[int, Tuple[float, float]] = {}  # movement vectors
        self._next_id: List[int] = [0]  # next ID to use
        self._distance_multiplier = distance_multiplier
        self._velocity_multiplier = velocity_multiplier
        self._velocity_decay_multiplier = velocity_decay_multiplier
        self._filter_value = filter_value

    def __call__(self, input_data: List[CentroidObject], *args, **kwargs):

        # if we are tracking nothing, just register all new objects
        if len(self._tracking_table) == 0:
            for obj in input_data:
                self._register_obj(obj)
        else:
            # if there are no new detections, so all current objects are lost for now
            if len(input_data) == 0:
                for idk, obj in enumerate(self._tracking_table):
                    self._lost(idk)

            else:

                used_idk = []
                used_idn = []

                # make an empty scoring table
                scoring_matrix = np.empty((len(self._tracking_table), len(input_data)), dtype=float)

                # calculate all the scores
                for idk, known_obj in enumerate(self._tracking_table):
                    for idn, new_obj in enumerate(input_data):
                        scoring_matrix[idk][idn] = self._score(known_obj, new_obj)

                can_match = True

                # match the best scores first
                while can_match:
                    idk, idn = np.unravel_index(scoring_matrix.argmin(), scoring_matrix.shape)
                    if scoring_matrix[idk, idn] < self._max_score:
                        scoring_matrix[idk] = 99
                        scoring_matrix[:, idn] = 99
                        self._dissapeared_objs[self._tracking_table[idk].ID] = 0
                        self._move_obj(idk, input_data[idn])
                        used_idk.append(idk)
                        used_idn.append(idn)
                    else:  # This means the best score in the list is now unmatchable
                        can_match = False

                for idk, obj in enumerate(self._tracking_table):
                    if idk not in used_idk:
                        self._lost(idk)

                for idn, obj in enumerate(input_data):
                    if idn not in used_idn:
                        self._register_obj(obj)

        self.next(self._tracking_table)

    def _lost(self, index):
        """
        call if an object has not been detected in this frame, this handles the rest
        :param index: index in tracking_table
        :return: None
        """

        # decay velocity
        self._tracking_table[index].velocity = (
            self._tracking_table[index].velocity_vector[0] * self._velocity_decay_multiplier,
            self._tracking_table[index].velocity_vector[1] * self._velocity_decay_multiplier)

        # move object ( robuster occlusion )
        self._tracking_table[index].centroid_object.centroid = self._calc_new_pos_guess(self.tracking_table[index])

        # add to the dissapeared counter
        self._dissapeared_objs[self._tracking_table[index].ID] = self._dissapeared_objs[
                                                                     self._tracking_table[index].ID] + 1
        if self._dissapeared_objs[self._tracking_table[index].ID] >= self._max_frame_loss:
            self._deregister_obj(self._tracking_table[index])

    @property
    def tracking_table(self) -> List[TrackedObject]:
        return self._tracking_table

    def calc_velocity(self,
                      known: CentroidObject,
                      new: CentroidObject) -> Tuple[float, float]:
        """
        Calculate the velocity for a CentroidObject moving from a -> b
        :param known: CentroidObject current state
        :param new: CentroidObject next state
        :return: Velocity vector Tuple[float, float]
        """

        new_centroid_x = new.centroid[0] * self._filter_value + \
                         known.centroid[0] * (1 - self._filter_value)
        new_centroid_y = new.centroid[1] * self._filter_value + \
                         known.centroid[1] * (1 - self._filter_value)

        velocity_vector = (known.centroid[0] - new_centroid_x,
                           known.centroid[1] - new_centroid_y)

        return velocity_vector

    def calc_velocity2(self,
                       known: CentroidObject,
                       new: CentroidObject,
                       old_velocity,
                       filter_value) -> Tuple[float, float]:
        """
        Calculate the velocity for a CentroidObject moving from a -> b
        :param known: CentroidObject current state
        :param new: CentroidObject next state
        :return: Velocity vector Tuple[float, float]
        """

        new_centroid_x = new.centroid[0] * self._filter_value + \
                         known.centroid[0] * (1 - self._filter_value)
        new_centroid_y = new.centroid[1] * self._filter_value + \
                         known.centroid[1] * (1 - self._filter_value)

        velocity_vector = ((new_centroid_x - known.centroid[0]) * filter_value + old_velocity[0] * (1 - filter_value),
                           (new_centroid_y - known.centroid[1]) * filter_value + old_velocity[1] * (1 - filter_value))

        return velocity_vector

    @staticmethod
    def _calc_new_pos_guess(obj: TrackedObject) -> Tuple[float, float]:
        """
        Calculates a guess for the new position of a TrackedObject
        :param obj: TrackedObject
        :return: Tuple[float, float] with guessed position
        """
        new_pos = (obj.centroid_object.centroid[0] + obj.velocity_vector[0],
                   obj.centroid_object.centroid[1] + obj.velocity_vector[1])

        return new_pos

    def _score(self, known: TrackedObject, new: CentroidObject) -> float:
        """
        Scoring function for the ShitTracker -- less is better for now
        Max score possible is 98
        :param known: TrackedObject out of tracking table
        :param new: new CentroidObject
        :return: score computed with the multipliers
        """

        # calculate a guess for the
        new_pos_guess = self._calc_new_pos_guess(known)

        # calculate the distance score (with respect to the new position)
        # dist_score = seuclidean(list(new_pos_guess), list(new.centroid))
        # dist_score = braycurtis(list(new_pos_guess), list(new.centroid))
        # dist_score = sqeuclidean(list(new_pos_guess), list(new.centroid))
        dist_score = euclidean(list(new_pos_guess), list(new.centroid))

        # calculate the presuamble new velocity
        new_velocity = self.calc_velocity2(known.centroid_object, new, known.velocity_vector, 0.2)

        # calculate the velocity score
        velocity_score = abs(known.velocity_vector[0] - new_velocity[0]) + \
                         abs(known.velocity_vector[1] - new_velocity[1])



        velocity_score = sqrt(velocity_score)
        # print(f"v_score:{velocity_score}")

        # calculate the overall score
        score = self._distance_multiplier * dist_score + self._velocity_multiplier * velocity_score

        # cap score
        if score > 98:
            score = 98

        #print(f"ID {known.ID} s: {score}")

        return score

    def _move_obj(self, index: int, new_obj: CentroidObject):
        """
        Use this to move the known object to the new position
        :param index: index in tracking table of object to move
        :param new_obj: object to move to
        :return: None
        """

        # get new centroid
        new_centroid_x = new_obj.centroid[0] * self._filter_value + \
                         self._tracking_table[index].centroid_object.centroid[0] * (1 - self._filter_value)
        new_centroid_y = new_obj.centroid[1] * self._filter_value + \
                         self._tracking_table[index].centroid_object.centroid[1] * (1 - self._filter_value)

        new_obj.centroid = (new_centroid_x, new_centroid_y)

        # get new velocity
        new_velocity = self.calc_velocity2(self._tracking_table[index].centroid_object,
                                           new_obj,
                                           self._tracking_table[index].velocity_vector,
                                           0.2)

        # change object values
        self._tracking_table[index].centroid_object.centroid = (new_centroid_x, new_centroid_y)
        self._tracking_table[index].velocity = new_velocity
        self._tracking_table[index].centroid_object.size = new_obj.size

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
        return f"{super().__str__()}MS : {self._max_score}; MFL : {self._max_frame_loss}"
