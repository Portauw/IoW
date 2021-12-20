from . import NextionDisplay
import os
from multiprocessing import Queue


class CronosScannerDisplay(NextionDisplay):

    def __init__(self, logging_q: Queue, **kwargs):
        super().__init__(logging_q=logging_q, **kwargs)

        self._n_estimated = 0
        self._n_max = 999
        self._n_in = 0
        self._n_out = 0
        self._ip = "no connection"
        self._ver = "1.0"
        self._avg_fps = 30
        self._wifi = 0

        self._pages = {'home': [self.send_n_estimated, self.send_n_max],
                       'detail': [self.send_n_in, self.send_n_out],
                       'settings': [self.send_ip, self.send_version, self.send_fps, self.send_wifi]}

        self._current_page = list(self._pages.keys())[0]
        self.send_cmd("sendme")

        pass

    def uart_poll(self):
        """
        call this as often as possible, this makes sure the right info is on the screen
        :return:
        """
        while self._port.in_waiting >= 4:
            data_in = self._port.read_until(bytes([255, 255, 255]))
            if data_in[0] == 102:  # 0x66
                self._current_page = list(self._pages.keys())[data_in[1]]
                # print("new page :")
                # print(self._current_page)
                for sender in self._pages[self._current_page]:
                    sender()

    def send_n_estimated(self):
        perc: float = float(self.n_estimated) / float(self.n_max)

        if perc < 0.8:
            color = 65535
        elif 0.8 <= perc < 1:
            color = 64897
        else:
            color = 63520

        self.send_cmd(f"n_estimated.txt=\"{str(self._n_estimated)}\"")
        self.send_cmd(f"n_estimated.pco={color}")
        pass

    def send_n_max(self):
        self.send_cmd(f"n_max.txt=\"{self._n_max}\"")
        pass

    def send_n_in(self):
        self.send_cmd(f"n_in.txt=\"{self._n_in}\"")
        pass

    def send_n_out(self):
        self.send_cmd(f"n_out.txt=\"{self._n_out}\"")
        pass

    def send_wifi(self):
        try:
            resp = os.popen("iwlist wlan0 scan | grep Quality").read().strip().split(' ')[0].split('=')[-1].split('/')
            wifi_strength = int((float(resp[0]) / float(resp[1])) * 100)
            self._wifi = wifi_strength
        except Exception as e:
            print(f"[DISPLAY] couldn't find wifi strength. Exception : {e}")
            self._wifi = 0
        self.send_cmd(f"wifi.val={self._wifi}")
        pass

    def send_ip(self, find_ip: bool = True):

        if find_ip:
            try:
                self._ip = os.popen('hostname -I').read().split(' ')[0]  # damn that fugly...
                if len(self._ip) < 5:
                    self._ip = 'no connection'
            except Exception as e:
                print(f"[DISPLAY] couldn't find ip. Exception : {e}")
                self._ip = 'unknown'

        self.send_cmd(f"ip.txt=\"{self._ip}\"")
        pass

    def send_version(self):
        self.send_cmd(f"ver.txt=\"{self._ver}\"")
        pass

    def send_fps(self):
        self.send_cmd(f"fps.txt=\"{self._avg_fps:.1f}\"")
        pass

    @property
    def n_estimated(self) -> int:
        return self._n_estimated

    @n_estimated.setter
    def n_estimated(self, value: int):
        self._n_estimated = value
        self.send_n_estimated()
        pass

    @property
    def incr_in(self):
        return None

    @incr_in.setter
    def incr_in(self, value: int):
        self._n_in = self._n_in + value
        self.send_n_in()
        pass

    @property
    def incr_out(self):
        return None

    @incr_out.setter
    def incr_out(self, value: int):
        self._n_out = self._n_out + value
        self.send_n_out()
        pass

    @property
    def incr_estimated(self):
        return None

    @incr_estimated.setter
    def incr_estimated(self, value: int):
        self._n_estimated = self._n_estimated + value
        self.send_n_estimated()
        pass

    @property
    def decr_estimated(self):
        return None

    @decr_estimated.setter
    def decr_estimated(self, value: int):
        self._n_estimated = self._n_estimated - value
        if self._n_estimated < 0:
            self._n_estimated = 0
        self.send_n_estimated()
        pass

    @property
    def n_max(self) -> int:
        return self._n_max

    @n_max.setter
    def n_max(self, value: int):
        self._n_max = value
        self.send_n_max()
        pass

    @property
    def n_in(self) -> int:
        return self._n_in

    @n_in.setter
    def n_in(self, value: int):
        self._n_in = value
        self.send_n_in()
        pass

    @property
    def n_out(self) -> int:
        return self._n_out

    @n_out.setter
    def n_out(self, value: int):
        self._n_out = value
        self.send_n_out()
        pass

    @property
    def wifi(self):
        return self._wifi

    @wifi.setter
    def wifi(self, value):
        self._wifi = value
        self.send_wifi()
        pass

    @property
    def ip(self) -> str:
        return self._ip

    @ip.setter
    def ip(self, value: str):
        self._ip = value
        self.send_ip()
        pass

    @property
    def version(self) -> str:
        return self._ver

    @version.setter
    def version(self, value: str):
        self._ver = value
        self.send_version()
        pass

    @property
    def avg_fps(self) -> float:
        return self._avg_fps

    @avg_fps.setter
    def avg_fps(self, value: float):
        self._avg_fps = value
        self.send_fps()
        pass

    def __str__(self):
        return f'[version: {self.version}] ' \
             f'[fps: {self.avg_fps}] ' \
             f'[n_estimated: {self.n_estimated}] ' \
             f'[n_in: {self.n_in}] ' \
             f'[n_out: {self.n_out}] ' \
             f'[max: {self.n_max}]'
