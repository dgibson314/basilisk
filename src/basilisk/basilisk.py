import argparse
import atexit
import configparser
from datetime import datetime
import httpx
import logging
import os
import random
import string
import sys
import time

THISDIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(THISDIR, "..", "..")
LOG_DIR = os.path.join(BASE_DIR, "logs")
SRC_DIR = os.path.join(THISDIR, "..")
DATA_DIR = os.path.join(BASE_DIR, "src", "data")
CONF_DIR = os.path.join(BASE_DIR, "conf")
CLIENT_DIR = os.path.join(THISDIR, "clients")
STRATS_DIR = os.path.join(THISDIR, "strats")

for path in [SRC_DIR, DATA_DIR, CLIENT_DIR, STRATS_DIR]:
    if path not in sys.path:
        sys.path.append(path)

from data.session import SessionEndpoint
from strats.example import ExampleStrat
from clients.td.td_client import TDClient

logger = logging.getLogger(__name__)
logging.basicConfig(filename=os.path.join(LOG_DIR, "session.log"), level=logging.DEBUG)

class BasiliskSession():

    def __init__(self):
        self.session_id = round(time.time())
        self.strats = None
        self.clients = None

    @staticmethod
    def get_clients():
        """
        Read conf file to get list of clients.
        """
        config = configparser.ConfigParser()
        config_file = os.path.join(CONF_DIR, "basilisk.conf")
        config.read(config_file)
        clients = config["CLIENTS"]["clients"]
        logging.info(f"Client list: {clients}")

        return clients

    @staticmethod
    def get_strats():
        """
        Read conf file to get list of strats.
        """
        config = configparser.ConfigParser()
        config_file = os.path.join(CONF_DIR, "basilisk.conf")
        config.read(config_file)
        strats = config["STRATEGIES"]["strats"]
        logging.info(f"Strategy list: {strats}")

        return strats


    def init_db_session(self):
        """
        Get client and strat info from conf files and populate new
        db BasiliskSession row.
        """
        date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        logging.info(f"Initializing new Basilisk session on {date}")
        self.clients = self.get_clients()
        self.strats = self.get_strats()
        new_session = {
            "session_id" : self.session_id,
            "date"       : date,
            "clients"    : self.clients,
            "strats"     : self.strats,
        }
        return SessionEndpoint.insert(new_session)

    def load_client_modules(self):
        raise NotImplementedError

    def load_strat_modules(self):
        raise NotImplementedError


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    sess = BasiliskSession()
    sess.init_db_session()
    client = TDClient()
    strat = ExampleStrat(client)
    strat.run()
