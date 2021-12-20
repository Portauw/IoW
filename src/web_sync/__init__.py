import time
from config import cfg
import json
from src.database import DbManager
from src.display_sync import DISPLAY_VERSION
from src.log import logger
#from .requests import login, people_entered, people_left
from .requests_cronos import login, people_entered, people_left
from threading import Thread, Event


UPDATE_INTERVAL = 2
LOGIN_INTERVAL = 5


class WebUpdater(Thread):
    def __init__(self, stop_event: Event, update_interval: float = UPDATE_INTERVAL, login_interval: float = LOGIN_INTERVAL):
        self._stop_event = stop_event
        self.update_interval = update_interval
        self.login_interval = login_interval
        self._update_in_progress = False
        self._db_manager = DbManager()
        self._location_id = None
        self._access_token = None
        self._stats = None
        self._logged_in = False
        self._next_login = time.time() + self.login_interval
        super().__init__()

    def login_handle(self):
        # Login to API
        try:
            self._logged_in, self._location_id, self._access_token, self._stats = login()
            n_max, current_stats = self._stats[0], self._stats[1]
            self._update_display_stats(n_max, current_stats)
            self._next_login = time.time() + self.login_interval
            logger.info(f"[WEB] Logged in!  Location_id:{self._location_id}; stats:{self._stats}")
        except Exception as e:
            logger.error(f"[WEB] Login Exception : {e}")

    def run(self) -> None:
        while not self._stop_event.is_set():
            if not self._update_in_progress:

                has_synced = False

                # Initialize
                self._update_in_progress = True

                if self._logged_in:
                    # Get unsynced data --> total number of people that entered and left since last sync
                    ids = self._db_manager.get_unsynced_records()  
                    response = None
                    for ID in ids:
                        if ID.n_people_left:
                            response = people_left(1, self._location_id, self._access_token)
                        elif ID.n_people_entered:
                            response = people_entered(1, self._location_id, self._access_token)

                        if response and response.status_code == 200:
                            # -- Intra-day-second-data
                            self._db_manager.update_synced_data([ID.id])
                            logger.info(f"[WEB] Updated record id {ID.id} : IN {ID.n_people_entered}; OUT {ID.n_people_left}")
                            has_synced = True

                if has_synced:
                    self.login_handle()

                if time.time() >= self._next_login:
                    self.login_handle()

                # Finalize
                self._update_in_progress = False
                time.sleep(self.update_interval)

    def _update_display_stats(self, n_max, current_stats):
        """ Update local db with latest display stats """
        self._db_manager.create_or_update_display_stats(DISPLAY_VERSION, {
            'n_max': n_max,
            'n_in_remote': current_stats['stat']['in'],
            'n_out_remote': current_stats['stat']['out'],
            'n_estimated': current_stats['stat']['actual']
        })
