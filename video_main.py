from src.ai.pipeline import Pipeline
from src.ai.pipeline.stages import FrameGrabber, Reshaper, ImagePreprocessor, AiEngine, ShitTracker, ShitTracker2, SchmittTrigger, SchmittToText
from src.ai.objects import zone as zn
from src.ai.objects import Zone
from src.ai.pipeline import Pipeline
import cv2
from utils import gui as gui
import time

if __name__ == '__main__':

    pipeline_stages = []

    # my_framegrabber = FrameGrabber("/Users/sam/PycharmProjects/edgebox_modular/video/mensen-tellen-joke-cropped.mp4")
    my_framegrabber = FrameGrabber("/Users/sam/Dropbox (Raccoons)/Projecten/Edgise/Telly/media/testing/passage_test_3_30fps.mp4")
    # my_framegrabber = FrameGrabber("/Users/sam/Dropbox (Raccoons)/Projecten/Edgise/Telly/media/testing/25-05-2020_16-01-11-video.mp4")
    pipeline_stages.append(my_framegrabber)

    my_reshaper = Reshaper((300, 300), flatten=False)
    pipeline_stages.append(my_reshaper)

    my_preprocessor = ImagePreprocessor(method='bgr2rgb')
    pipeline_stages.append(my_preprocessor)

    my_engine = AiEngine("models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite", class_list=[0])
    # my_engine = AiEngine("models/head_detector_v2_320x320_ssd_mobilenet_v2_quant_edgetpu.tflite", class_list=[0])
    pipeline_stages.append(my_engine)

    #my_tracker = ShitTracker(max_dist=0.15, frame_loss_max=10, filter_value=0.4)
    #my_tracker = Kalman(frame_loss_max=20, max_distance=0.25, class_labels=None)
    my_tracker = ShitTracker2()
    pipeline_stages.append(my_tracker)

    # my_zone1 = zn.Zone((0.0, 0.0), (1.0, 0.25), True)
    # my_zone2 = zn.Zone((0.0, 0.25), (1.0, 0.30), False)
    # my_zone3 = zn.Zone((0.0, 0.0), (1.0, 1.0), True)
    my_zone1 = zn.Zone((0.0, 0.0), (0.45, 1.0), True)
    my_zone2 = zn.Zone((0.45, 0.0), (0.55, 1.0), False)
    my_zone3 = zn.Zone((0.55, 0.0), (1.0, 1.0), True)
    my_schmitt_trigger = SchmittTrigger([my_zone1, my_zone2, my_zone3])
    pipeline_stages.append(my_schmitt_trigger)

    my_stt = SchmittToText(method="people_inout", label_file="utils/labels/labels_head.txt", print_to_console=False)
    pipeline_stages.append(my_stt)

    my_gui = gui.Gui((300, 300), labels_file="utils/labels/labels_head.txt")
    start_time = 0

    my_pipe = Pipeline(stages=pipeline_stages)
    wait_for_keypress = True

    while True:

        my_pipe()

        elapsed_time = time.time() - start_time
        start_time = time.time()
        fps = int(round(1 / elapsed_time, 0))

        key_exit = my_gui(tracking_table=my_tracker.tracking_table,
                          zones=my_schmitt_trigger.zones,
                          fps=fps, frame=my_reshaper.output,
                          text=my_stt.output)

        while wait_for_keypress:
            if cv2.waitKey(1) & 0xFF == ord('n'):
                wait_for_keypress = False

        if key_exit:
            break

    my_framegrabber.source.release()
    cv2.destroyAllWindows()
