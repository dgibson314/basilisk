import configparser
import json
import logging
import os
import sys
import time

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(THIS_DIR, "..", "..")
CLIENT_DIR = os.path.join(THIS_DIR, "..")

for path in [SRC_DIR, CLIENT_DIR]:
    if path not in sys.path:
        sys.path.append(path)

from base_client.base_client import BaseClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_conf_info():
    config = configparser.ConfigParser()
    config.read("td.conf")
    return (config['credentials']['CLIENT_ID'], config['credentials']['REDIRECT_URI'])

class TDClient(BaseClient):
    
    provides = []

    def __init__(self):
        self._token_path = "td_tokens.json"
        self._client_id, self._redirect_uri = get_app_info()
        self._refresh_lifetime = None
        self._auth_death_time = None

    def connect(self):
        pass

    def calc_auth_death(self):
        """
        Get the time when the auth token will expire.
        The time will be the number of seconds since epoch.
        For safety we set the lifetime to be a few minutes
        before the max value.
        """
        with open(self._token_path) as f:
            data = json.load(f)

        auth_lifetime = data["expires_in"]
        current_time = round(time.time())

        max_death_time = current_time + auth_lifetime
        death_time = max_death_time - 300
        logger.debug("TDClient - auth token death time: %d" % death_time)

        self._auth_death_time = death_time


    def calc_refresh_death(self):
        """
        Get the time when the refresh token will expire.
        The time will be the number of seconds passed since epoch.
        For safety, we'll end up requesting a new refresh token
        a week before the old one expires.
        """
        WEEK_IN_SEC = 604800

        with open(self._token_path) as f:
            data = json.load(f)

        refresh_lifetime = data["refresh_token_expires_in"]
        current_time = round(time.time())

        max_death_time = current_time + refresh_lifetime
        death_time = max_death_time - WEEK_IN_SEC
        logger.debug("TDClient - refresh token death time: %d" % death_time)

        if data.get("refresh_death_time") is None:
            logger.debug("TDClient - Writing refresh token death time to json file")
            data["refresh_death_time"] = death_time_
            with open(self._token_path, "w") as f:
                json.dump(data, f)
