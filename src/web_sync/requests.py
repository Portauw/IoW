import requests
import json
from src.log import logger
from src.database import DbManager
from src.display_sync import DISPLAY_VERSION
from config import LOGIN_URL, INCREASE_URL, DECREASE_URL, GET_STATE_URL, USERNAME, PASSWORD


HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json'
}
DATA_AUTH = {
    'username': USERNAME,
    'password': PASSWORD
}


def login():
    """ Authenticate, and get current server status """
    try:
        login_response = requests.post(LOGIN_URL, headers=HEADERS, data=DATA_AUTH)
        if login_response.status_code == 200:
            login_data = json.loads(login_response.text)

            # Get and update display stats
            n_max = login_data['location']['personMaxAllowed']

            current_stats = login_data['statOfToday']

            #FIXME: receive None from backend beginning of the day but should be zero !!!!!
            if(current_stats['stat'] is None):
                current_stats = {'stat': {'in': 0, 'out': 0, 'actual': 0}}

            # Get location id
            location_id = login_data['location']['id']

            # Get access token
            access_token = login_data['login']['id']

            return True, location_id, access_token, (n_max, current_stats)
        return False, None, None, None
    except Exception as e:
        logger.error(e)
    return False, None, None, None


def people_entered(n: int, location_id: str, access_token: str):
    """ Update server with people that entered the room """
    return _update_room_change(n, True, location_id, access_token)


def people_left(n: int, location_id: str, access_token: str):
    """ Update server with people that left the room """
    return _update_room_change(n, False, location_id, access_token)


def _update_room_change(n: int, has_entered: bool, location_id: str, access_token: str):
    try:
        data = {
            'locationId': location_id,
            'count': n
        }
        params = (
            ('locationId', location_id),
            ('access_token', access_token)
        )
        url = INCREASE_URL if has_entered else DECREASE_URL
        return requests.post(url, headers=HEADERS, params=params, data=data)
    except Exception as e:
        logger.error(e)
