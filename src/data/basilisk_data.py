import configparser
import os
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

    def create_td_token_tabe(self):
        """
        CREATE TABLE IF NOT EXISTS td_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auth_token TEXT NOT NULL,
            auth_token_end INTEGER,
            refresh_token TEXT NOT NULL,
            refresh_token_end INTEGER
        )
        """
        pass

    @staticmethod
    def get_db_location():
        config = configparser.ConfigParser()
        config.read(os.path.join(CONFDIR, "db.conf"))
        return (config["LOCATION"])

if __name__ == "__main__":
    DB = Database()
