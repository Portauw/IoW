from src.ai.pipeline.stages import PipelineStage


class Scratchpad(PipelineStage):
    """
    Keeps the last value in memory, does not call a next function!
    """

    def __init__(self, **kwargs):
        """
        Constructor method of Scratchpad
        """
        super().__init__(prefix="SP", **kwargs)
        self._pad = None

    def __call__(self, input_data, *args, **kwargs):
        """
        save input_data until the next one arrives.
        Will not call a next function!
        """

        self._pad = input_data

    def __str__(self):
        return f"{super().__str__()}Scratchpad"
