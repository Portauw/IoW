from src.ai.pipeline.stages import PipelineStage
from typing import Callable, List


class SchmittToText(PipelineStage):
    """
    Just a class which will allow us to convert the SchmittTrigger output to human readable text

    This is still kind of dirty with a method for each demo
    """

    def factory(self, method: str = "default") -> Callable:
        """
        Factory that returns the right preprocessing function according the the method string
        :param method: method as string
        :return: Callable function
        """

        if method == "people_inout":
            self._temp_data_dict['in'] = 0
            self._temp_data_dict['out'] = 0
            conv_func = self._people_inout
        elif method == "highway":
            self._temp_data_dict['lane0'] = []
            self._temp_data_dict['lane1'] = []
            self._temp_data_dict['lane2'] = []
            conv_func = self._triple_lane_highway_classed
        elif method == "parking_inout":
            self._temp_data_dict['in'] = []
            self._temp_data_dict['out'] = []
            conv_func = self._parking_inout
        else:
            conv_func = self._default_conv

        return conv_func

    def __init__(self, method: str = "default", label_file: str = None, print_to_console: bool = True, **kwargs):
        """
        Constructor method

        :param method: for different printing styles/applications
        :type method: string
        :param label_file: path to label file
        :type label_file: string
        :param print_to_console: if the output should be printed to the console
        :type print_to_console: bool
        """
        super().__init__(prefix="STT", **kwargs)

        if label_file is not None:
            with open(label_file, 'r') as f:
                pairs = (l.strip().split(maxsplit=1) for l in f.readlines())
                self._labels = dict((int(k), v) for k, v in pairs)
        else:
            self._labels = None

        self._temp_data_dict = {}  # Dict to hold temporary data
        self._print_to_console = print_to_console
        self._method = method
        self._conv_func = self.factory(method=method)
        self._output: str = "Invalid"

    @property
    def method(self) -> str:
        return self._method

    @property
    def output(self) -> str:
        return str(self._output)

    def get_output(self) -> str:
        """
        Getter for output

        :return: self.output
        """
        return str(self._output)

    def __call__(self, input_data: List, *args, **kwargs):
        """
        Invoke interpreter

        :param input_data: the output from the previous stage
        :type input_data: List
        """
        self._output = self._conv_func(input_data)
        if self._print_to_console:
            print(f"{super().__str__()}{self.output}")
        self.next(self._output)

    def _default_conv(self, input_data: List) -> str:
        """
        The default conversion

        :param input_data: List with data from previous stage
        :type input_data: List
        :return string with readable output for previous stage
        """
        str_out = ""
        for movement in input_data:
            if self._labels is not None:
                lbl_txt = self._labels[movement[0]]
            else:
                lbl_txt = str(movement[0])
            str_out = str_out + f"({lbl_txt}) from z{movement[1][0]} to z{movement[1][-1]}\n"

        if len(str_out) < 3:
            return self._output
        else:
            return str_out

    def _people_inout(self, input_data: List) -> str:
        """
        Checks if a person went in or out the building

        :param input_data: List with data from previous stage
        :type input_data: List
        :return string with readable output for previous stage
        """
        for movement in input_data:
            if movement[1][-1] == 2:
                self._temp_data_dict['in'] = self._temp_data_dict['in'] + 1
            elif movement[1][-1] == 0:
                self._temp_data_dict['out'] = self._temp_data_dict['out'] + 1
        str_out = f"In : {self._temp_data_dict['in']}\nOut: {self._temp_data_dict['out']}"

        return str_out

    def _parking_inout(self, input_data: List) -> str:
        """
        Checks if a car went in or out the parking

        :param input_data: List with data from previous stage
        :type input_data: List
        :return string with readable output for previous stage
        """
        # append the new counts to the lane
        for movement in input_data:
            if movement[1][-1] == 2:
                self._temp_data_dict['in'].append(movement[0])
            elif movement[1][-1] == 0:
                self._temp_data_dict['out'].append(movement[0])

        in_count = [[x, self._temp_data_dict['in'].count(x)] for x in set(self._temp_data_dict['in'])]
        out_count = [[x, self._temp_data_dict['out'].count(x)] for x in set(self._temp_data_dict['out'])]
        str_out = f"IN  : "

        for entry in in_count:
            str_out = str_out + f"{self._labels[entry[0]]}:{entry[1]}, "
        str_out = str_out + "\nOUT : "

        for entry in out_count:
            str_out = str_out + f"{self._labels[entry[0]]}:{entry[1]}, "

        return str_out

    def _triple_lane_highway_classed(self, input_data: List) -> str:
        """
        Checks in which lane a car has driven

        :param input_data: List with data from previous stage
        :type input_data: List
        :return string with readable output for previous stage
        """
        # appends the new counts to the lane
        for movement in input_data:
            if movement[1][-1] == 4:
                self._temp_data_dict['lane0'].append(movement[0])
            elif movement[1][-1] == 5:
                self._temp_data_dict['lane1'].append(movement[0])
            elif movement[1][-1] == 6:
                self._temp_data_dict['lane2'].append(movement[0])

        # Counts how many of each class have been counted
        lanes = [[[x, self._temp_data_dict['lane0'].count(x)] for x in set(self._temp_data_dict['lane0'])],
                 [[x, self._temp_data_dict['lane1'].count(x)] for x in set(self._temp_data_dict['lane1'])],
                 [[x, self._temp_data_dict['lane2'].count(x)] for x in set(self._temp_data_dict['lane2'])]]

        # Text placeholder
        str_out = ""

        # Find out how many lines we will need
        lines = 0
        for lane in lanes:
            if len(lane) > lines:
                lines = len(lane)

        # Output the counts to readable text
        for i in range(0, lines, 1):
            for lane in lanes:
                if len(lane) > i:
                    entry = lane[i]
                    str_out = str_out + f"      {self._labels[entry[0]]}:{entry[1]}          "
                else:
                    str_out = str_out + "                     "  # or leave a white space if there is nothing yet

            # if there will be another line to print, add a newline
            if i < (lines-1):
                str_out = str_out + "\n"

        return str_out
