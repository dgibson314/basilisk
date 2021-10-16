import configparser
import json
import logging
import os
import requests
import sys
import time

THISDIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(THISDIR, "..", "..", "..", "..")
SRC_DIR = os.path.join(BASE_DIR, "src")
DATA_DIR = os.path.join(SRC_DIR, "data")
CONF_DIR = os.path.join(BASE_DIR, "conf")
CLIENT_DIR = os.path.join(THISDIR, "..")

for path in [SRC_DIR, CLIENT_DIR, DATA_DIR]:
    if path not in sys.path:
        sys.path.append(path)

from base_client.base_client import BaseClient
from data.basilisk_session import BasiliskSession

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_URL = "https://api.tdameritrade.com/v1/oauth2"

class TokenError(Exception):
    pass

class TDClient(BaseClient):
    
    provides = []

    def __init__(self):
        self._client_id, self._redirect_uri = self.get_conf_info()
        self._refresh_lifetime = None
        self._access_end_time = None
        self._token_path = "td_tokens.json"

    @staticmethod
    def get_conf_info():
        config = configparser.ConfigParser()
        config_file = os.path.join(CONF_DIR, "td.conf")
        config.read(config_file)
        return (config["credentials"]["CLIENT_ID"], config["credentials"]["REDIRECT_URI"])

    def refresh_access_token(self):
        """
        Requests a new access token.
        Returns None if request fails.
        """
        refreshtoken = self.refreshtoken()
        payload = {
            "grant_type"    : "refresh_token",
            "refresh_token" : refreshtoken,
            "client_id"     : self._client_id + "@AMER.OAUTHAP"
        }
        try:    
            r = requests.post(BASE_URL + "/token", data=payload)
            r.raise_for_status()
        except Exception as e:
            logger.error("Unable to refresh access token. Exception: " % e)
            return None

        response_data = r.json()
        new_access_token = response_data["access_token"]
        expires_in = response_data["expires_in"]
        safe_expiration = self.calc_access_end(expires_in)
        data = {
            "access_token" : new_access_token,
            "access_ends"  : safe_expiration,
        }

        with open(self._token_path, "w") as f:
            json.dump(data, f)

    def refreshtoken(self):
        with open(self._token_path) as f:
            data = json.load(f)

            refreshtoken = data.get("refresh_token")
            if not refreshtoken:
                raise TokenError

            return refreshtoken

    @staticmethod
    def calc_access_end(lifetime):
        """
        Get the time when the access token will expire.
        The time will be the number of seconds since epoch.
        For safety we set the lifetime to be a few minutes
        before the max value.
        """
        current_time = round(time.time())

        max_end_time = current_time + lifetime
        end_time = max_end_time - 300

        return end_time
    
    def calc_refresh_end(self):
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

        max_end_time = current_time + refresh_lifetime
        end_time = max_end_time - WEEK_IN_SEC
        logger.debug("TDClient - refresh token end time: %d" % end_time)

        if data.get("refresh_end_time") is None:
            logger.debug("TDClient - Writing refresh token end time to json file")
            data["refresh_end_time"] = end_time_
            with open(self._token_path, "w") as f:
                json.dump(data, f)


if __name__ == "__main__":
    client = TDClient()
