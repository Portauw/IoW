from src.ai.pipeline.stages import FrameGrabber as fg, Reshaper as rs, ImagePreprocessor, AiEngine, ShitTracker, ShitTracker2, SchmittTrigger
from src.ai.objects import zone as zn
from typing import Dict, List, Tuple
from src.ai.objects import CentroidObject, TrackedObject
import numpy as np
import time
import cv2

colortable = {
    "White": (255, 255, 255),
    "Black": (0, 0, 0),
    "Red": (0, 0, 255),
    "Lime": (0, 255, 0),
    "Blue": (255, 0, 0),
    "Yellow": (0, 255, 255),
    "Cyan": (255, 255, 0),
    "Magenta": (255, 0, 255),
    "Silver": (192, 192, 192),
    "Gray": (128, 128, 128),
    "Maroon": (0, 0, 128),
    "Olive": (0, 128, 128),
    "Green": (0, 128, 0),
    "Purple": (128, 0, 128),
    "Teal": (128, 128, 0),
    "Navy": (128, 0, 0)
}


class Gui:
    """
    This class will make sure that everything gets drawn
    """

    def __init__(self,
                 window_size=(640, 480),
                 labels_file: str = None,
                 window_name: str = "Video"):
        """
        Constructor method

        :param window_size: Gui window size, format = (width, height), defaults to (640,480)
        """
        self.window_size = window_size
        self.width = window_size[0]
        self.height = window_size[1]
        self.line_list = {}

        self._window_name = window_name

        self.labels = None
        self.labels_file = labels_file

        if self.labels_file is not None:
            with open(self.labels_file, 'r') as f:
                pairs = (l.strip().split(maxsplit=1) for l in f.readlines())
                self.labels = dict((int(k), v) for k, v in pairs)

        cv2.namedWindow(self._window_name)

    def __call__(self, tracking_table, zones, fps, frame, text: str = ""):
        """
        Show the output

        :param tracking_table: list of TrackedObjects
        :param zones: List of zones
        :param fps: frames per second
        :param frame: output image
        :param text: text to display at bottom of image
        :return: None
        """

        frame = self.draw_text_window(frame, text)
        frame = self.draw_objects_2(tracking_table, frame)
        frame = self.draw_zones(zones, frame)
        frame = self.draw_fps(fps, frame)

        cv2.imshow(self._window_name, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return 1
        else:
            return 0

    def draw_text_window(self, frame, txt):

        # split the lines
        lines = txt.split("\n")

        # get the height of 1 line
        (txt_width, txt_height), txt_baseline = cv2.getTextSize(lines[0], cv2.FONT_HERSHEY_COMPLEX, 0.5, 1)

        # calculate total height
        tot_height = (txt_height+txt_baseline) * len(lines) + 10

        # add white bar to frame
        text_frame = np.full((tot_height, frame.shape[1], 3), 255, dtype=np.uint8)
        frame = np.concatenate((frame, text_frame), axis=0)

        # print te lines
        for i, line in enumerate(lines):
            cv2.putText(frame,
                        line,
                        (10, self.height + (txt_height + 5)*(i+1)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 0),
                        1,
                        cv2.LINE_AA)

        return frame

    def draw_objects_2(self, tracking_table: List[TrackedObject], frame) -> np.ndarray:
        key_list = list(self.line_list.keys())

        for obj in tracking_table:

            # get color code
            color_code = colortable[(list(colortable)[obj.ID % 16])]

            # Calculate the luminance of the color
            luminance = (0.2126 * color_code[2] + 0.7151 * color_code[1] + 0.0721 * color_code[0])/255.

            # Draw lines
            if obj.ID in self.line_list.keys():
                # Append to points list
                self.line_list[obj.ID].append(obj.centroid_object.get_abs_centroid(self.window_size))

                # draw all the lines
                for i in range(1, len(self.line_list[obj.ID])-1, 1):
                    cv2.line(frame,
                             self.line_list[obj.ID][i-1],
                             self.line_list[obj.ID][i],
                             color_code,
                             2,
                             lineType=cv2.LINE_AA)

                key_list.remove(obj.ID)
            else:
                self.line_list[obj.ID] = [obj.centroid_object.get_abs_centroid(self.window_size)]

            # set text color as black or white according to luminance
            if luminance < 0.6:
                text_color = (255, 255, 255)
            else:
                text_color = (0, 0, 0)

            # draw bounding box
            cv2.rectangle(frame, obj.centroid_object.get_abs_p1(self.window_size),
                          obj.centroid_object.get_abs_p2(self.window_size), color_code, 2)

            # draw centre circle
            cv2.circle(frame, obj.centroid_object.get_abs_centroid(self.window_size), 15, color_code, -1)

            # draw ID text
            (id_width, id_height), id_baseline = cv2.getTextSize(str(obj.ID), cv2.FONT_HERSHEY_COMPLEX, 0.5, 1)
            text_x = obj.centroid_object.get_abs_centroid(self.window_size)[0] - int(id_width/2)
            text_y = obj.centroid_object.get_abs_centroid(self.window_size)[1] + int(id_height/2)
            cv2.putText(frame, str(obj.ID), (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)

            # get label text
            if self.labels is not None:
                lbl_txt = self.labels[obj.centroid_object.label]
            else:
                lbl_txt = str(obj.centroid_object.label)

            self._draw_label(frame,
                             lbl_txt,
                             obj.centroid_object.get_abs_centroid(self.window_size),
                             color_code,
                             text_color,
                             offset=(20, -6))

            self._draw_label(frame,
                             str(f"x{obj.velocity_vector[0]:.3f};y{obj.velocity_vector[1]:.3f}"),
                             obj.centroid_object.get_abs_centroid(self.window_size),
                             color_code,
                             text_color,
                             anchor_right=True,
                             offset=(-20, -6))

        for key in key_list:
            del self.line_list[key]

        return frame

    @staticmethod
    def _draw_label(frame, text: str,
                    loc: Tuple[int, int],
                    color_code, text_color,
                    anchor_right: bool = False,
                    offset: Tuple[int, int] = (0, 0)):

        # get label text size
        (label_width, label_height), label_baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_COMPLEX, 0.5, 1)

        if anchor_right:
            left_top = (loc[0] - label_width, loc[1])
            bottom_right = (loc[0] + 1, loc[1] + label_height + label_baseline)
        else:
            left_top = (loc[0], loc[1])
            bottom_right = (loc[0] + label_width + 1, loc[1] + label_height)

        # left_top = (left_top[0] + offset[0], left_top[1] + offset[1])
        left_top = tuple(x + y for x, y in zip(left_top, offset))
        bottom_right = tuple(x + y for x, y in zip(bottom_right, offset))

        # draw label background
        cv2.rectangle(frame,
                      left_top,
                      bottom_right,
                      color_code,
                      -1)

        # draw label text
        cv2.putText(frame,
                    text,
                    (left_top[0]+2, bottom_right[1]-label_baseline+2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    text_color,
                    1,
                    cv2.LINE_AA)

    def draw_objects(self, tracking_table, frame) -> np.array:
        """
        draw the centroid point and bounding boxes of all the current objects inside the gui window

        :param model_output: output list of the model running tin the AI engine
        :type model_output: List[CentroidObject]        :

        :param frame: video frame
        :type frame: np.array
        """

        # delete the lines if nothing is being tracked
        if not tracking_table:
            self.line_list = {}

        for cen_id, cen in tracking_table.items():
            color_code = colortable[(list(colortable)[cen_id % 16])]
            cv2.rectangle(frame, cen.get_abs_p1(self.window_size), cen.get_abs_p2(self.window_size), color_code, 3)
            cv2.circle(frame, cen.get_abs_centroid(self.window_size), 15, color_code, 2)

            # create new line entry for new centroids
            if cen_id not in self.line_list:
                self.line_list[cen_id] = []

            # add new point to the already existing centroid line
            else:
                self.line_list[cen_id].append(cen.get_abs_centroid(self.window_size))

            # loop through the line_list and draw al the points
            for line in self.line_list:
                cen_list = self.line_list[line]

                if (len(cen_list) > 1):
                    prev_point = cen_list[0]
                    for x in range(len(cen_list)):
                        cv2.line(frame, prev_point, cen_list[x], color_code, 3)
                        prev_point = cen_list[x]

            text_x = cen.get_abs_centroid(self.window_size)[0] - 5
            text_y = cen.get_abs_centroid(self.window_size)[1] + 3
            cv2.putText(frame, str(cen_id), (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_code, 1, cv2.LINE_AA)

        return frame

    def draw_zones(self, zones, frame) -> np.array:
        """
        draw the defined zones inside the gui window

        :param zones: list of Zones
        :type frame: np.array
        """

        zone_id = 0

        for zone in zones:
            coord_p1 = (int(zone.p1[0] * self.width), int(zone.p1[1] * self.height))
            coord_p2 = (int(zone.p2[0] * self.width), int(zone.p2[1] * self.height))
            cv2.rectangle(frame, coord_p1, coord_p2, (34, 254, 254), 1)
            cv2.putText(frame, f"Z{zone_id}", (coord_p1[0] + 10, coord_p1[1] + 20), cv2.FONT_HERSHEY_SIMPLEX,
                        0.3, (34, 254, 254), 1, cv2.LINE_AA)
            zone_id = zone_id + 1

        return frame

    def draw_fps(self, fps, frame):
        fps = "FPS: " + str(fps)
        cv2.putText(frame, fps, (int(0.82 * self.width), int(0.05 * self.height)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 50, 0), 1, cv2.LINE_AA)
        return frame


##################################
# BELOW CODE IS ONLY FOR TESTING #
##################################
if __name__ == '__main__':

    # my_framegrabber = fg.FrameGrabber("video/Edgise-1up-lowres-shifted.mp4")
    my_framegrabber = fg.FrameGrabber("video/Edgise-parking-fulltest-lowres_shifted.mp4")
    my_reshaper = rs.Reshaper((300, 300), True)

    my_zone1 = zn.Zone((0.0, 0.0), (1.0, 0.2), True)
    my_zone2 = zn.Zone((0.0, 0.4), (1.0, 1.0), True)
    my_gui = Gui((640, 480))
    start_time = 0

    while True:
        ret, original_frame = my_framegrabber()  # output a frame
        if not ret:
            break
        frame = my_reshaper(original_frame)  # output a flattened frame

        elapsed_time = time.time() - start_time
        start_time = time.time()
        fps = int(round(1 / elapsed_time, 0))

        key_exit = my_gui({}, [my_zone1, my_zone2], fps, original_frame, True)

        if (key_exit):
            break

    my_framegrabber.source.release()
    cv2.destroyAllWindows()
