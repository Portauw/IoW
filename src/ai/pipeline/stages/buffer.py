from src.ai.pipeline.stages import PipelineStage


class Buffer(PipelineStage):
    """
    Will buffer it's input
    """

    def __init__(self, **kwargs):
        """
        Constructor method
        """
        super().__init__(prefix="BUF", **kwargs)
        self._buffer = []

    def __call__(self, input_data, *args, **kwargs):
        """
        will append input_data to the list
        """
        self._buffer.append(input_data)

        self.next(input_data)

    def pop_buffer(self):
        return self._buffer.pop(0)

    @property
    def empty(self):
        return len(self._buffer) == 0

    def __str__(self):
        return f"{super().__str__()}Buffer | length : {len(self._buffer)}"
