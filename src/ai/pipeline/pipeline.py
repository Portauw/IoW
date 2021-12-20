from typing import List
from src.ai.pipeline.stages import PipelineStage


class Pipeline:
    """
    A pipeline object, has a list of stages, each stages calls the next one itself.
    Every stage should be a PipelineStage, which has a __call__ method that takes "input_data" + args + kwargs
    """

    def __init__(self, stages: List[PipelineStage]):
        """
        Initializer of a pipeline
        :param stages: list of the stages (must be callable)
        """
        self.stages = stages
        self._init = False

        if len(self.stages) > 2:
            self.init_stages()

    def __call__(self):
        """
        This will run the pipeline once by calling the first stage, which will then call the next and so on.
        if the stages have not been initialized yet, this will do nothing besides printing something
        :return:
        """
        if self._init:
            self.stages[0]()
        else:
            print("(Pipeline) Stages not initialized.")

    @property
    def init(self) -> bool:
        """
        This wil return the init status of the pipeline.
        Read only
        :return: init stage as bool
        """
        return self._init

    def init_stages(self):
        """
        This initialised the stages by attaching the next stage to each stage, except for the last one.
        :return:
        """
        for i in range(len(self.stages)-2, -1, -1):
            self.stages[i].nxt = [self.stages[i+1]]

        self._init = True

    def __str__(self):
        out = ""
        for stage in self.stages:
            out += f" | {str(stage)}"

        return out


