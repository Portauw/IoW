import numpy as np
from src.ai.objects import CentroidObject
from typing import List
from src.ai.pipeline.stages import PipelineStage
import tflite_runtime.interpreter as tflite
import platform


class AiEngine(PipelineStage):
    """
    Engine to run your AI SSD detection model using tflite_runtime
    """

    def __init__(self, model_path: str, min_score: float = 0.5, top_k: int = 25, class_list: List[int] = [], **kwargs):
        """
        Constructor method of AiEngine, creates a PipelineStage which will run inference on an input image.
        This will not do any reshaping or preprocessing.

        :param model_path: path to model
        :type model_path: str
        :param min_score: minimum score of detection
        :type min_score: float
        :param top_k: max # of detections
        :type top_k: int
        """
        super().__init__(prefix="AI", **kwargs)
        self._model_path = model_path
        self._min_score = min_score
        self._top_k = top_k
        self._platform = platform.system()
        self._scale = (1, 1)
        self._class_list = class_list

        self._engine = self._make_interpreter()
        self._input_details = self._engine.get_input_details()
        self._output_details = self._engine.get_output_details()
        self._engine.allocate_tensors()

        self._detections: List[CentroidObject] = []

    @property
    def output_details(self):
        return self._output_details

    @property
    def input_details(self):
        return self._input_details

    @property
    def detections(self) -> List[CentroidObject]:
        return self._detections

    def __call__(self, input_data, *args, **kwargs):
        """
        Invoke interpreter

        expects a 2D array!

        :param input_data: 2D array which will be run through the tflite_interpreter
        :param args: Ignored
        :param kwargs: Ignored
        """

        # it is still batch based, so expand to get to the [1, w, h, c] shape
        input_data = np.expand_dims(input_data, axis=0)

        # load data into the tensor
        self._engine.set_tensor(self._input_details[0]['index'], input_data)

        # run the inference
        self._engine.invoke()

        count = min(int(self._engine.get_tensor(self._output_details[3]['index'])), self._top_k)
        boxes = self._engine.get_tensor(self._output_details[0]['index'])[0][:count+1]
        class_ids = self._engine.get_tensor(self._output_details[1]['index'])[0][:count+1]
        scores = self._engine.get_tensor(self._output_details[2]['index'])[0][:count+1]

        result = [CentroidObject(label=int(class_ids[i]), score=scores[i], bbox=boxes[i])
                  for i in range(count) if scores[i] >= self._min_score
                  and (class_ids[i] in self._class_list or not self._class_list)]

        # print(result)

        self.next(result)

    def _make_interpreter(self) -> tflite.Interpreter:
        """
        This will create a tflite interpreter depending on if the supplied model was an EdgeTPU model or not
        :return: tflite interpreter
        """

        model_file = self._model_path

        exp_delegates = []

        if self._model_path.endswith('edgetpu.tflite'):
            edgetpu_shared_lib = {
                'Linux': 'libedgetpu.so.1',
                'Darwin': 'libedgetpu.1.dylib',
                'Windows': 'edgetpu.dll'
            }[self._platform]

            model_file, *device = self._model_path.split('@')

            try:
                exp_delegates = [tflite.load_delegate(edgetpu_shared_lib, {'device': device[0]} if device else {})]
            except ValueError:
                print('Did you try to use an EdgeTPU that does not exist?')
                exp_delegates = []

        engine = tflite.Interpreter(model_path=model_file, experimental_delegates=exp_delegates)

        return engine

    def __str__(self) -> str:
        """
        Readable String
        """
        return f"{super().__str__()}Model path : {self._model_path}\n"
