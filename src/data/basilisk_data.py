import configparser
import sqlite3 as sl

THISDIR = os.path.dirname(os.path.abspath(__file__))
CONFDIR = os.path.join(THISDIR, "..", "..", "conf")

class Database():

    def  __init__(self):
        self._location = self.get_db_location()
        self.connection = sl.connect(_location)
        self.cursor = self.connection.cursor()

    def close(self):
        self.connection.close()

    def execute(self, data):
        self.cursor.execute(data)

    def __enter__(self):
        return self

    def __exit__(self, ext_type, exc_value, traceback):
        self.cursor.close()
        if isinstance(exc_value, Exception):
            self.connection.rollback()
        else:
            self.connection.commit()
        self.connection.close()

    @staticmethod
    def get_db_location():
        config = configparser.ConfiParser()
        config.read(os.path.join(CONFDIR, "db.conf"))
        return (config["LOCATION"])
