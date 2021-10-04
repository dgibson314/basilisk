import os
import requests
import sys
import time

from td_client import TDClient

BASE_URL = "https://api.tdameritrade.com/v1/oauth2"

class TestClient(TDClient):

    def __init__(self):
        super().__init__()
