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

from base_client.base_client import LevelOne
from data.tokens import TokensEndpoint

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_URL = "https://api.tdameritrade.com/v1/"
AUTH_URL = BASE_URL + "oauth2"

class TokenError(Exception):
    pass

class TDClient(LevelOne):
    
    provides = ["equity"]

    def __init__(self):
        credentials = self.get_credentials_info()
        self._client_id = credentials["CLIENT_ID"]
        self._redirect_uri = credentials["REDIRECT_URI"]
        self._account_id = credentials["ACCOUNT_ID"]
        self._refresh_token = None
        self._access_token = None
        self._access_end = None

    @staticmethod
    def get_credentials_info():
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

        if TokensEndpoint.update("td", data):
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
            logger.error(f"Unable to refresh access token. Exception: {e}")
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
        if TokensEndpoint.update("td", data):
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
            row = TokensEndpoint.get("td")
            access_token = row.session_token
            access_end = row.session_token_end
            # Values may be null if this is the first time we're starting the DB?
            # Get a fresh access token
            if (access_token == "null" or access_end == "null" or
                access_token is None or access_end is None):
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
                token = TokensEndpoint.get("td").auth_token
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

    def make_get_request(self, url, params=None, headers=None):
        """
        Basic method for making a GET request to the TD Ameritrade API.
        """
        if headers is None:
            headers = {"Authorization": f"Bearer {self.access_token()}"}
        try:
            r = requests.get(url, headers=headers, params=params)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Request to {url} failed with exception: {e}")
            # TODO: consider handling this by tryint refresh_access_token() before raising
            raise
        response_data = r.json()
        return response_data

    #######################################
    ############## QUOTES #################
    #######################################

    def get_quote(self, *symbols, field=None):
        """
        Gets quote info for one or more symbols.
        If a specific field (i.e. bid price, ask price, volatility, etc)
        is needed, a dict mapping of symbols to their fields is returned.
        Otherwise all quote info is returned.
        """
        url = BASE_URL + "marketdata/quotes" params = {"symbol" : ",".join(symbols)}
        data = self.make_get_request(url, params=params)

        if field:
            results = {}
            for symbol in symbols:
                results[symbol] = data[symbol][field]
            return results

        return data

    def get_bid_price(self, *symbols):
        return self.get_quote(*symbols, field="bidPrice")

    def get_bid_size(self, *symbols):
        return self.get_quote(*symbols, field="bidSize")

    def get_ask_price(self, *symbols):
        return self.get_quote(*symbols, field="askPrice")

    def get_ask_size(self, *symbols):
        return self.get_quote(*symbols, field="askSize")

    def get_open_price(self, *symbols):
        return self.get_quote(*symbols, field="openPrice")

    def get_high_price(self, *symbols):
        return self.get_quote(*symbols, field="highPrice")

    def get_low_price(self, *symbols):
        return self.get_quote(*symbols, field="lowPrice")

    def get_close_price(self, *symbols):
        return self.get_quote(*symbols, field="closePrice")

    def get_volatility(self, *symbols):
        return self.get_quote(*symbols, field="volatility")

    def get_high_52(self, *symbols):
        return self.get_quote(*symbols, field="52WkHigh")

    def get_low_52(self, *symbols):
        return self.get_quote(*symbols, field="52WkLow")

    def get_fundamentals(self, symbol):
        url = BASE_URL + "instruments"
        params = {
            "symbol" : symbol,
            "projection" : "fundamental"
        }
        return self.make_get_request(url, params=params)

    ###################################
    ########## PRICE HISTORY ##########
    ###################################

    def get_price_history(self, symbol, period_type="day", period=10,
            frequency_type="minute", frequency=1, end_date=None, start_date=None,
            extended_hours=true):
        """
        Gets the price history for a symbol.
        Args:
        - symbol: the symbol to get the history of
        - period_type: type of period to show. Valid values are
            * day
            * month
            * year
            * ytd (year to date)
        - period: number of periods to show. Valid periods by period_type
            * day: 1, 2, 3, 4, 5, 10
            * month: 1, 2, 3, 6
            * year: 1, 2, 3, 5, 10, 15, 20
            * ytd: 1
        - frequency_type: type of frequency with which a new candle is formed. Valid
            frequency types by period_type
            * day: minute
            * month: daily, weekly
            * year: daily, weekly, monthly
            * ytd: daily, weekly
        - frequency: number of the frequency_type to be included in each candle. Valid
            frequencies by frequency_type
            * minute: 1, 5, 10, 15, 30
            * daily: 1
            * weekly: 1
            * monthly: 1
        - end_date: End date as milliseconds since epoch. If start_date and end_date are
            provided, period should not be provided.
        - start_date: Start date as millisconds since epoch. If start_date and end_date are
            provided, period should not be provided.
        - extended_hours: True to return extended hours data, false for regular market hours only.
        """
        raise NotImplementedError

    def get_market_hours(self, market, date):
        """
        Retrieve market hours for specified single market.
        Args:
        - market: the market we're requesting hours for. Valid options are
            * EQUITY
            * OPTION
            * BOND
            * FOREX
            * FUTURE
        - date: the date for which market hours info is requested. Valid ISO-8601 formats are
            * yyyy-MM-dd
            * yyyy-MM-dd'T'HH:mm:ssz
        """
        raise NotImplementedError


if __name__ == "__main__":
    client = TDClient()
    print(client.get_bid_price("AAPL", "GOOGL"))
