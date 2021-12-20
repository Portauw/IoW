import time
from config import cfg
# from src.database import DbManager
from threading import Thread, Event
# from queue import Queue
from .nextion_display import NextionDisplay
from .cronos_scanner_display import CronosScannerDisplay
from typing import Dict
from multiprocessing import Queue as mpQueue
from src.base import EdgiseBase

DISPLAY_VERSION = "1.0"

DATA_TRANSLATOR: Dict = {'fps': CronosScannerDisplay.avg_fps,
                         'n_estimated': CronosScannerDisplay.n_estimated,
                         'n_in': CronosScannerDisplay.n_in,
                         'n_out': CronosScannerDisplay.n_out,
                         'n_max': CronosScannerDisplay.n_max,
                         'avg_fps': CronosScannerDisplay.avg_fps,
                         'incr_in': CronosScannerDisplay.incr_in,
                         'incr_out': CronosScannerDisplay.incr_out,
                         'incr_estimated': CronosScannerDisplay.incr_estimated,
                         'decr_estimated': CronosScannerDisplay.decr_estimated,
                         'version_text': CronosScannerDisplay.version}


class DisplayUpdater(Thread, EdgiseBase):
    def __init__(self, stop_event: Event, data_q: mpQueue, logging_q: mpQueue, **kwargs):
        self._stop_event = stop_event
        self._data_q = data_q
        # self._db_manager: DbManager = DbManager()
        self._display: CronosScannerDisplay = self._initialize_display(logging_q)
        # self._display.n_in = self._db_manager.get_entered()
        # self._display.n_out = self._db_manager.get_left()
        self._display.n_in = 0
        self._display.n_out = 0
        self._last_logger_line: str = ''

        Thread.__init__(self)
        EdgiseBase.__init__(self, name="DISPLAY", logging_q=logging_q)

    def _data_parser(self, incoming: Dict) -> int:
        """
        loads whatever is in the dict into the display object
        :param incoming: Dict containing new data
        :return: # of correct data values
        """
        counter = 0

        for key, value in incoming.items():
            if key in DATA_TRANSLATOR:
                DATA_TRANSLATOR[key].fset(self._display, value)
                counter += 1
            else:
                self.error(f"[DISPLAY] Unknown data key/value : {key} : {value} -- Ignoring")

        return counter

    def run(self) -> None:
        while not self._stop_event.is_set():
            self._display.uart_poll()

            # Check if there is some incoming data
            while not self._data_q.empty():
                incoming = self._data_q.get()
                self._data_parser(incoming)

            # log if anything changed
            self._log()

            time.sleep(cfg.screen_update_interval)
        self.info(f"Quitting.")

    @staticmethod
    def _initialize_display(logging_q: mpQueue):
        # Initialize Cronos scanner display
        display = CronosScannerDisplay(logging_q)
        # display.version = DISPLAY_VERSION
        display.n_max = 10

        return display

    def _log(self):
        # Update display with latest stats
        if self._display is not None:
            logger_str = str(self._display)

            if logger_str != self._last_logger_line:
                self._last_logger_line = logger_str
                self.info(logger_str)
