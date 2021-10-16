import configparser
from contextlib import contextmanager
import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import sqlite3 as sl

THISDIR = os.path.dirname(os.path.abspath(__file__))
BASEDIR = os.path.join(THISDIR, "..", "..")
CONFDIR = os.path.join(BASEDIR, "conf")

Base = declarative_base()

def get_db_location():
    config = configparser.ConfigParser()
    config.read(os.path.join(CONFDIR, "db.conf"))
    return os.path.join(BASEDIR, str(config["LOCATION"]["location"]))

ENGINE = create_engine(f"sqlite:///{get_db_location()}")

@contextmanager
def db_session():
    global ENGINE
    session = sessionmaker(bind=ENGINE)

    try:
        yield session
        session.commit
    except:
        session.rollback
        raise
    finally:
        session.close()


class BasiliskSession(Base):
    __tablename__ = "basilisk_session"
    session_id = Column(Integer, primary_key=True)
    date = Column(Integer)
    clients = Column(String)
    strats = Column(String)
    access_token = Column(String)
    access_end = Column(Integer)
    refresh_token = Column(String)
    refresh_end = Column(Integer)

    def __init__(session_id, date, clients, strats):
        self.id = session_id
        self.date = date
        self.clients = clients
        self.strats = strats

class TDTokens(Base):
    __tablename__ = "td_tokens"
    refresh_token = Column(String, primary_key=True)
    refresh_end = Column(Integer)
    access_token = Column(String)
    access_end = Column(Integer)

Base.metadata.create_all(ENGINE)
