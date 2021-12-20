from src.ai.pipeline.stages import PipelineStage
from typing import List


class SimpleCounter(PipelineStage):
    """
    This will simply count the amount of objects
    """

    def __init__(self, **kwargs):
        """
        Constructor method of SimpleCounter
        """
        super().__init__(prefix="SC", **kwargs)
        self._output = 0

    def __call__(self, input_data: List, *args, **kwargs):
        """
        Count the objects

        :param input_data: List
        """

        self._output = len(input_data)

        self.next(self._output)

    def __str__(self):
        return f"{super().__str__()}Simple counter -- Last output : {self._output}"
