import time
import config
import json
from src.database import DbManager
from src.display_sync import DISPLAY_VERSION
from src.log import logger
#from .requests import login, people_entered, people_left
from .requests_cronos import login, people_entered, people_left
from threading import Thread, Event


UPDATE_INTERVAL = 5


class WebUpdater(Thread):
    def __init__(self, stop_event: Event, interval: float = UPDATE_INTERVAL):
        self._stop_event = stop_event
        self._interval = interval
        self._update_in_progress = False
        self._db_manager = DbManager(config.DATABASE_URI)
        self._logged_in = False
        super().__init__()

    def run(self) -> None:
        while not self._stop_event.is_set():
            if not self._update_in_progress:
                # try:
                    # login()
                    # sync_backend()
                        # while (n_in > 0) 
                            ## cronos central api heeft geen aantal. Dus een api call per increase
                            # increase(locationId, token)
                            # if (success)
                            # update n_in??
                        # while (n_out > 0)
                            ## cronos central api heeft geen aantal. Dus een api call per decrease
                            # decrease(location, token)   
                            # if (success) 
                            # update n_out???
                    # getCurrentStats()
                    # updateDisplay()
                # except


                # Initialize
                self._update_in_progress = True

                # Login to API
                try:
                    self._logged_in, location_id, access_token, stats = login()
                    n_max, current_stats = stats[0], stats[1]
                    self._update_display_stats(n_max, current_stats)
                except Exception as e:
                    logger.error(e)

                if self._logged_in:
                    # Get unsynced data --> total number of people that entered and left since last sync
                    ids, n_out, n_in = self._db_manager.get_unsynced_data()  
                    #for i in range(n_in):
                    #    response = people_entered(1, location_id, access_token)
                    #    if response and response.status_code == 200:
                    #      self._db_manager.update_synced_data(ids)
                    # Update server with new data
                    logger.info(f'[WEB] Update server: {n_in} entered and {n_out} left since last sync')
                    response = None

                    # -- People that entered
                    if n_in > 0:
                        response = people_entered(n_in, location_id, access_token)
                    # -- People that left
                    if n_out > 0:
                        response = people_left(n_out, location_id, access_token)

                    # Update local database
                    if response and response.status_code == 200:
                        # -- Intra-day-second-data
                        self._db_manager.update_synced_data(ids)
                        
                # Finalize
                self._update_in_progress = False
                time.sleep(self._interval)

    def _update_display_stats(self, n_max, current_stats):
        """ Update local db with latest display stats """
        self._db_manager.create_or_update_display_stats(DISPLAY_VERSION, {
            'n_max': n_max,
            'n_in_remote': current_stats['stat']['in'],
            'n_out_remote': current_stats['stat']['out']
        })
