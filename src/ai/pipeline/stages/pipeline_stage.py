from typing import List, Callable
from abc import abstractmethod


class PipelineStage:
    """
    Base class to inherit from when creating a stage for a @Pipeline
    """

    @abstractmethod
    def __init__(self, prefix: str = "DEF", nxt: List[Callable] = None):

        if not nxt:
            nxt = [self.default_nxt]
        self._nxt = nxt
        self._prefix = prefix
        pass

    @property
    def nxt(self) -> List[Callable]:
        """
        get the list of next method's
        :return: list of all the next functions
        """
        return self._nxt

    @nxt.setter
    def nxt(self, new_nxt: List[Callable]):
        """
        Set a new list of next methods to chain
        :param new_nxt: list of methods to chain behind this one
        """
        self._nxt = new_nxt

    def next(self, *args, **kwargs):
        """
        Run the next methods in the chain
        :param data: data to pass through
        :return: None
        """
        for nxt in self.nxt:
            nxt(*args, **kwargs)

    def default_nxt(self, *args, **kwargs):
        # print(f"{self} -- no callable nxt() function implemented, pipeline end")
        # print(args)
        # raise NotImplementedError  # Dit geeft mss nog wat veel clutter als niet alles klaar is?
        pass

    @abstractmethod
    def __call__(self, input_data, *args, **kwargs):
        print(f"{self}__call__ not implemented, passing through")

        for nxt in self._nxt:
            nxt(input_data)

        pass

    @abstractmethod
    def __str__(self) -> str:
        return f"({self._prefix}) "

