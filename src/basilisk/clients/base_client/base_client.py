import random
import string
import sys
import time
import uuid

from abc import ABC, abstractmethod

class BaseClient(ABC):
    pass

class LevelOne(BaseClient):
    @abstractmethod
    def get_bid_price(self):
        raise NotImplementedError

    @abstractmethod
    def get_ask_price(self):
        raise NotImplementedError

    @abstractmethod
    def get_volatility(self):
        raise NotImplementedError
    pass
