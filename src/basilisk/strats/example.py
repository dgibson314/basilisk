import logging
import os
import sys

THISDIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(THISDIR, "..", "..", "..")
SRC_DIR = os.path.join(THISDIR, "..", "..")

class ExampleStrat():
    requires = ["equity"]

    def __init__(self, client):
        self.client = client

    def run(self):
        symbol = "AAPL"
        vol = self.client.get_volatility(symbol)
        print(f"{symbol} volatility: {vol}")
