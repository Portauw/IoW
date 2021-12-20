import numpy as np
from typing import Callable
from src.ai.pipeline.stages import PipelineStage


class ImagePreprocessor(PipelineStage):
    """
    PipelineStage for preprocessing
    """

    def factory(self, method: str = "default") -> Callable:
        """
        Factory that returns the right preprocessing function according the the method string
        :param method: method as string
        :return: Callable function
        """
        prep_func = dict(mobilenet_v3=self.mobilenet_v3,
                         bgr2rgb=self.bgr2rgb,
                         mobilenet_v2_ali=self.mobilenet_v2_ali,
                         default=self.default)
        return prep_func[method]

    def __init__(self, method: str = "default", **kwargs):
        """
        Initialized the preprocessor
        :param method: method name as string
        :param kwargs: passed to super class (PipelineStage)
        """
        super().__init__(prefix="PRE", **kwargs)
        self.method = method
        self.function = self.factory(method=method)

    def __call__(self, input_data: np.array, *args, **kwargs):
        """
        Runs the supplied input image through the preprocessing function
        :param input_data: input image as np array
        :return:
        """
        self.next(self.function(input_data))

    @staticmethod
    def default(input_data: np.array) -> np.array:
        """
        Does nothing at all
        :param input_data: input image as np array
        :return: unaltered input image as np array
        """
        return input_data

    @staticmethod
    def bgr2rgb(input_data: np.array) -> np.array:
        """
        this just swaps the channels around
        :param input_data: BGR input image as np array
        :return: RGB image as np array
        """
        return input_data[..., ::-1]

    @staticmethod
    def mobilenet_v3(input_data: np.array) -> np.array:
        """
        classic kind of preprocessing which will "normalize" an image, but the normalization might be a bit wonky
        :param input_data:
        :return:
        """

        output_data = input_data[..., ::-1] / 255.
        mean = [0.485, 0.456, 0.406]
        std = [0.229, 0.224, 0.225]
        for i in range(3):
            output_data[..., i] -= mean[i]
            output_data[..., i] /= std[i]

        lowest_val = output_data.min()
        val_range = output_data.max() - lowest_val

        output_data = ((output_data + lowest_val) * (1/val_range) * 255).astype('uint8')

        return output_data

    @staticmethod
    def mobilenet_v2_ali(input_data: np.array) -> np.array:
        """
        Dit is voor Ali
        :param input_data: image
        :return: preprocessed image
        """
        output_data = input_data[..., ::-1] / 255.
        mean = [0.485, 0.456, 0.406]
        std = [0.229, 0.224, 0.225]
        for i in range(3):
            output_data[..., i] -= mean[i]
            output_data[..., i] /= std[i]
        output_data = output_data.astype('float32')
        return output_data

    def __str__(self) -> str:
        """
        Returns human readable string
        """
        return f"{super().__str__()}{self.function.__name__}"
