import numpy as np
import cv2
from src.ai.objects import CentroidObject
from src.ai.objects import TrackedObject
from typing import Dict, List, Tuple
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from collections import defaultdict
from src.ai.pipeline.stages import PipelineStage


class Kalman(PipelineStage):

    def __init__(self, frame_loss_max=20, max_distance=0.5, class_labels=None, **kwargs):
        super().__init__(prefix="KAL", **kwargs)
        self.tracked_centroids: Dict[int, TrackedObject] = {}
        self.kalman_tracks: Dict[int, cv2.KalmanFilter] = {}
        self.disappeared = defaultdict(int)
        self.object_id = 0
        self.frame_loss_max = frame_loss_max
        self.max_distance = max_distance
        self.class_labels = class_labels
        return

    def __call__(self, input_data: List[CentroidObject], *args, **kwargs):
        #filtered_list = self.filter_input_data(input_data)
        #for input_data in filtered_list:
         #   if not input_data:
          #      continue
            #else:
        new_bbox = [list(centroids.bbox) for centroids in input_data]  # [[(x1,y1),(x2,y2), ...]]
        old_centroids = [list(v.centroid_object.centroid) for k, v in self.tracked_centroids.items()]
        new_centroids = [list(centroids.centroid) for centroids in input_data]
        if not old_centroids and not new_centroids:
            pass
            # return self.tracked_centroids
        elif not old_centroids and new_centroids:
            self.register_track(input_data)
            # return self.tracked_centroids
        elif old_centroids and not new_centroids:
            # input self.disappearing should not be track id but rather index corresponding to id
            # not very pretty but does the trick for now
            idx_list = list(range(0, len(old_centroids)))
            tracks_to_be_deleted = self.disappearing_tracks(idx_list)
            self.deregister_track(tracks_to_be_deleted)
            # return self.tracked_centroids
        else:
            cost_matrix = self.calculate_cost_matrix(new_centroids, old_centroids)
            # assignment of objects to tracks
            matched, unmatched_detection, unmatched_tracks = self.hungarian_algorithm(cost_matrix)
            self.register_track(list(np.array(input_data)[unmatched_detection]))
            self.match(new_bboxes=new_bbox, new_centroids=new_centroids, matched_objects=matched)
            tracks_to_delete = self.disappearing_tracks(unmatched_tracks)
            self.deregister_track(tracks_to_delete)
            # return self.tracked_centroids

        self.next(self.tracking_table)

    @property
    def tracking_table(self) -> List[TrackedObject]:
        return list(self.tracked_centroids.values())

    def filter_input_data(self, input_data: List[CentroidObject]):
        filtered_list = [[]]
        if not self.class_labels:
            filtered_list.append(input_data)
        elif not input_data:
            pass
        else:
            for label in self.class_labels:
                obj_with_label = [obj for obj in input_data if obj.label == label]
                filtered_list.append(obj_with_label)
                input_data = set(input_data) - set(obj_with_label)

        return filtered_list

    # possibly make this a general function for different types of cost functions
    def calculate_cost_matrix(self, new_centroids: List[List[int]], old_centroids: List[List[int]]) -> np.ndarray:
        # calculate cost on all bbox points or just centroids ?
        cost_matrix = cdist(np.array(new_centroids), np.array(old_centroids), metric="braycurtis")
        return cost_matrix

    def hungarian_algorithm(self, cost_matrix: np.ndarray):
        # actual hungarian algorithm
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        # row_id indicates the detection id
        # col_id indicates the track id
        # indices larger than certain threshold -> unmatched
        unmatched_detections = [detect for detect in range(0, cost_matrix.shape[0]) if detect not in row_ind]
        unmatched_tracks = [track for track in range(0, cost_matrix.shape[1]) if track not in col_ind]
        matched_tuples = list(zip(row_ind, col_ind))
        valid_tuples = []
        for (row_idx, col_idx) in matched_tuples:
            if cost_matrix[row_idx][col_idx] > self.max_distance:
                unmatched_detections.append(row_idx)
                unmatched_tracks.append(col_idx)
            else:
                valid_tuples.append((row_idx, col_idx))

        return valid_tuples, unmatched_detections, unmatched_tracks

    def create_kalman_filter(self, new_centroid) -> cv2.KalmanFilter:
        # for clarity
        state_dim = 8
        measure_dim = 4
        kalman_filter = cv2.KalmanFilter(state_dim, measure_dim)  # state vector
        # measurement model
        kalman_filter.measurementMatrix = np.array([[1, 0, 0, 0, 0, 0, 0, 0],
                                                    [0, 1, 0, 0, 0, 0, 0, 0],
                                                    [0, 0, 1, 0, 0, 0, 0, 0],
                                                    [0, 0, 0, 1, 0, 0, 0, 0]], np.float32)
        # transition model
        kalman_filter.transitionMatrix = np.array([[1, 0, 0, 0, 1, 0, 0, 0],
                                                   [0, 1, 0, 0, 0, 1, 0, 0],
                                                   [0, 0, 1, 0, 0, 0, 1, 0],
                                                   [0, 0, 0, 1, 0, 0, 0, 1],
                                                   [0, 0, 0, 0, 1, 0, 0, 0],
                                                   [0, 0, 0, 0, 0, 1, 0, 0],
                                                   [0, 0, 0, 0, 0, 0, 1, 0],
                                                   [0, 0, 0, 0, 0, 0, 0, 1]],
                                                  np.float32)  # dt = 35, should be framerate
        kalman_filter.processNoiseCov = np.identity(8,
                                                    dtype=np.float32) * 0.01  # should find a way to find this correctly
        # fix performance of list comprehensions
        # initialization of the state vector
        bbox = new_centroid.bbox
        kalman_filter.statePre = np.array([bbox[0][0], bbox[0][1], bbox[1][0], bbox[1][1], 0, 0, 0, 0],
                                          dtype=np.float32).reshape(8, 1)
        kalman_filter.statePost = np.array([bbox[0][0], bbox[0][1], bbox[1][0], bbox[1][1], 0, 0, 0, 0],
                                           dtype=np.float32).reshape(8, 1)
        return kalman_filter

    def register_track(self, new_centroids: List[CentroidObject]) -> None:
        for new_centroid in new_centroids:
            # register centroid object and create a kalman filter for it
            self.tracked_centroids[self.object_id] = TrackedObject(ID=self.object_id, velocity=(0.0, 0.0),
                                                                   centroid_object=new_centroid)
            self.disappeared[self.object_id] = 0
            kalman_filter = self.create_kalman_filter(new_centroid)
            self.kalman_tracks[self.object_id] = kalman_filter
            # increment ids for now
            self.object_id += 1
        return None

    def disappearing_tracks(self, unmatched_tracks: List[int]) -> List[int]:
        tracks_to_be_deleted = []
        for unmatched_track in unmatched_tracks:
            track_key = list(self.tracked_centroids.keys())[unmatched_track]
            self.disappeared[track_key] += 1
            if self.disappeared[track_key] > self.frame_loss_max:
                tracks_to_be_deleted.append(track_key)

        #for track_id in self.tracked_centroids.keys():
        #    if self.disappeared[track_id] > self.frame_loss_max:
        #        tracks_to_be_deleted.append(track_id)
        return tracks_to_be_deleted

    def deregister_track(self, tracks_to_be_deleted: List[int]) -> None:
        for track_id in tracks_to_be_deleted:
            del self.tracked_centroids[track_id]
            del self.disappeared[track_id]
            del self.kalman_tracks[track_id]
        return None

    def match(self, new_bboxes: List[list], new_centroids: List[list], matched_objects: List[tuple]) -> None:
        for match in matched_objects:
            detection_id = match[0]
            print(match)
            print(match[1])
            print(list(self.tracked_centroids.keys()))
            track_id = list(self.tracked_centroids.keys())[match[1]]
           # track_id = match[1] not possible
            new_measurement = np.array(new_bboxes[detection_id], dtype=np.float32).reshape(4, 1)  # [(x1,y1),(x2,y2)]

            self.kalman_tracks[track_id].predict()
            corrected_measurement = self.kalman_tracks[track_id].correct(new_measurement)

            # format corrected data
            corrected_bbox = [tuple(corrected_measurement[0:2].flatten()), tuple(corrected_measurement[2:4].flatten())]
            corrected_v = [tuple(corrected_measurement[4:6].flatten()), tuple(corrected_measurement[6:8].flatten())]

            tracked_obj = self.tracked_centroids[track_id]
            tracked_obj.centroid_object.bbox = corrected_bbox
            tracked_obj.bbox_velocity = corrected_v

            self.disappeared[track_id] = 0

            # self.tracked_centroids[track_id].set_centroid(tuple(corrected_centroid.flatten()))
        return None
