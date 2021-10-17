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
from data.tokens import Tokens

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_URL = "https://api.tdameritrade.com/v1/"
AUTH_URL = BASE_URL + "oauth2"

class TokenError(Exception):
    pass

class TDClient(BaseClient):
    
    provides = []

    def __init__(self):
        credentials = self.get_credentials_info()
        self._client_id = credentials["CLIENT_ID"]
        self._redirect_uri = credentials["REDIRECT_URI"]
        self._account_id = credentials["ACCOUNT_ID"]
        self._refresh_token = None
        self._access_token = None
        self._access_end = None

    @staticmethod
    def get_credentials_info(field):
        config = configparser.ConfigParser()
        config_file = os.path.join(CONF_DIR, "td.conf")
        config.read(config_file)
        return config["credentials"]

   ###########################################
   ############# AUTHENTICATION ##############
   ###########################################

    def refresh_refresh_token(self):
        """
        Requests a new refresh token. If the request succeeds we update
        the local refresh token as well as the DB fields.
        Returns the token on success.
        Returns None if request fails.
        """
        refresh_token = self.refresh_token()
        payload = {
            "grant_type"    : "refresh_token",
            "refresh_token" : refresh_token,
            "access_type"   : "offline",
            "client_id"     : self._client_id + "@AMER.OAUTHAP"
        }
        try:
            r = requests.post(AUTH_URL + "/token", data=payload)
            r.raise_for_status()
        except Exception as e:
            logger.error("Unable to refresh refresh token. Exception: " % e)
            return None

        response_data = r.json()
        new_refresh_token = response_data["refresh_token"]
        expires_in = response_data["expires_in"]
        safe_expiration = self.calc_refresh_end(expires_in)
        data = {
            "auth_token" : new_refresh_token,
            "auth_token_end" : safe_expiration
        }

        # Update local version
        self._refresh_token = new_refresh_token

        if Tokens.update("td", data):
            print("Refreshing DB succeeded")
        else:
            print("Failed to update DB with new refresh token")
            return None

        return self._refresh_token

    def refresh_access_token(self):
        """
        Requests a new access token. If the request succeeds we update
        the local access token as well as the DB fields.
        Returns the token on success.
        Returns None if request fails.
        """
        refresh_token = self.refresh_token()
        payload = {
            "grant_type"    : "refresh_token",
            "refresh_token" : refresh_token,
            "client_id"     : self._client_id + "@AMER.OAUTHAP"
        }
        try:    
            r = requests.post(AUTH_URL + "/token", data=payload)
            r.raise_for_status()
        except Exception as e:
            logger.error("Unable to refresh access token. Exception: " % e)
            return None

        response_data = r.json()
        new_access_token = response_data["access_token"]
        expires_in = response_data["expires_in"]
        safe_expiration = self.calc_access_end(expires_in)
        data = {
            "session_token" : new_access_token,
            "session_token_end"  : safe_expiration,
        }
     
        # Update local version
        self._access_token = new_access_token
        self._access_end = safe_expiration

        # Update DB with new token.
        if Tokens.update("td", data):
            print("Refreshing access token succeeded.")
        else:
            print("Refreshing access token failed.")
            return None

        return self._access_token

    def access_token(self):
        """
        Returns the access token. Uses the locally cached version if it
        exists and is fresh, else gets it from the DB.
        """
        current_time = round(time.time())
        # If local access token exists and is fresh use it
        if self._access_token is not None:
            if self._access_end is not None and self._access_end > current_time:
                return self._access_token
        # Otherwise check the DB
        else:
            row = Tokens.get("td")
            access_token = row.session_token
            access_end = row.session_token_end
            # Values may be null if this is the first time we're starting the DB?
            # Get a fresh access token
            if access_token == "null" or access_end == "null":
                return self.refresh_access_token()

            # If the DB token is stale request a new one
            if access_end < current_time:
                return self.refresh_access_token()

            self._access_token = access_token
            self._access_end = access_end
            return self._access_token

    def refresh_token(self):
        """
        Returns refresh_token. If we have it stored locally use that,
        else get it from the DB and update the local version.
        TODO: We should have a check of some kind to check whether the token
        is stale or not.
        """
        if self._refresh_token is not None:
            return self._refresh_token
        else:
            try:
                token = Tokens.get("td").auth_token
                self._refresh_token = token
                return token
            except:
                print("Failed to fetch refresh token")
                return None


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
  
    @staticmethod
    def calc_refresh_end(lifetime):
        """
        Get the time when the refresh token will expire.
        The time will be the number of seconds passed since epoch.
        For safety, we'll end up requesting a new refresh token
        a week before the old one expires.
        """
        WEEK_IN_SEC = 604800

        current_time = round(time.time())

        max_end_time = current_time + lifetime
        end_time = max_end_time - WEEK_IN_SEC

        return end_time

    #######################################
    ######### INSTRUMENT DATA #############
    #######################################

    def get_quote(self, symbol):
        url = BASE_URL + f"/marketdata/{symbol}/quotes"
        headers = {"Authorization": f"Bearer {self.access_token()}"}
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Unable to fetch quote for {symbol}. Exception: {e}" )
            return None

        response_data = r.json()
        return response_data

    def get_fundamentals(self, symbol):
        url = BASE_URL + "/instruments"
        headers = {"Authorization": f"Bearer {self.access_token()}"}
        payload = {
            "symbol" : symbol,
            "projection" : "fundamental"
        }
        try:
            r = requests.get(url, headers=headers, params=payload)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Unable to fetch fundamentals for {symbol}. Exception: {e}")
            return None

        response_data = r.json()
        return response_data

if __name__ == "__main__":
    client = TDClient()
    print(client.get_fundamentals("AAPL"))
