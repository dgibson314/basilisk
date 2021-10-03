import random
import string
import sys
import time
import uuid

from abc import ABC, abstractmethod

class BaseClient(ABC):
    @abstractmethod
    def connect(self):
        pass
