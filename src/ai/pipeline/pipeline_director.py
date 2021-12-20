from src.ai.pipeline import Pipeline
from threading import Thread


class PipelineDirector:
    """
    Pipeline director class
    """

    def __init__(self, pipeline: Pipeline = None, threaded: bool = True):
        """
        Initialization function
        :param pipline: pipeline to direct
        :param threaded: Should it run in a different thread
        """

        self.threaded = threaded
        self.pipeline = pipeline

        if self.threaded:
            self.pipeline_t = Thread(target=self.pipeline)
        else:
            self.pipeline_t = None

    def start_loop(self):

        pass

