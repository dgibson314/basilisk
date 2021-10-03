import argparse
import atexit
import httpx
import logging
import random
import string
import sys
import tda
import time
import uuid


'''
Supposed to encapsulate relevant info about current session.
'''

logger = logging.getLogger(__name__)


class BasiliskSession():

    def __init__(self):
        self.session_id = self.create_session_id()
        self._session_start = time.time()
        self._session_end = None

    @staticmethod
    def make_webdriver(browser="Chrome"):
        from selenium import webdriver

        logger.info("Creating webdriver")

        if browser != "Chrome":
            logger.error(f"Unable to create webdriver for browser {browser} !!!")
            raise NotImplemented

        driver = webdriver.Chrome()
        atexit.register(lambda: driver.quit())
        return driver

    @staticmethod
    def create_session_id():
        prefix = "basilisk_"
        postfix = "".join(random.choice(string.ascii_letters) for _ in range(10))
        return f"{prefix}{postfix}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="Output debug messages", action="store_true")
    parser.add_argument("-c", "--client", help="Client to connect with", default="TD")

    args = vars(parser.parse_args())

