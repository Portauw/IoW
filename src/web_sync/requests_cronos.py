import requests
from requests.auth import HTTPBasicAuth
import json
from src.log import logger
from src.database import DbManager
from src.display_sync import DISPLAY_VERSION
from config import cfg


def login():
    """ Authenticate, and get current server status """
    try:
        login_response = requests.post(cfg.cronosLoginUrl, auth=HTTPBasicAuth(cfg.cronosUsername, cfg.cronosPassword),
                                       headers={'Content-Type': 'application/jwt'})

        if login_response and login_response.status_code == 200:
            token = login_response.text 
            location_response = requests.get(cfg.cronosGetLocationUrl,
                                             headers={'Authorization': 'Bearer ' + token})

            if location_response and location_response.status_code == 200:
                location_data = json.loads(location_response.text)
                n_max = location_data['PersonMaxAllowed']                  
                current_stats_response = requests.get(cfg.cronosGetStatsUrl,
                                                      headers={'Authorization': 'Bearer ' + token})

                if current_stats_response and current_stats_response.status_code == 200:
                    current_stats_data = json.loads(current_stats_response.text)
                    current_stats = {'stat': {'in': current_stats_data['In'], 'out': current_stats_data['Out'], 'actual': current_stats_data['Actual']}}
                    return True, location_data['Id'], token, (n_max, current_stats)

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
    url = cfg.cronosIncreaseUrl if has_entered else cfg.cronosDecreaseUrl
    try:
        orig_response = requests.post(url, headers={'Authorization': 'Bearer ' + access_token})
        
        #current_stats_data = json.loads(orig_response.text)
        #current_stats = {'stat': {'in': current_stats_data['In'], 'out': current_stats_data['Out'], 'actual': current_stats_data['Actual']}}

        #orig_response.text = json.dumps(current_stats)
        
        return orig_response 
    except Exception as e:
        logger.error(e)
        logger.error(url)
