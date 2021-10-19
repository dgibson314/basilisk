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
    SESSION_FACTORY = sessionmaker(bind=ENGINE,expire_on_commit=False)

    session = SESSION_FACTORY()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class BasiliskSession(Base):
    __tablename__ = "basilisk_session"
    session_id = Column(Integer, primary_key=True)
    clients = Column(String)
    strats = Column(String)

    def __init__(self, session_id, clients, strats):
        self.id = session_id
        self.clients = clients
        self.strats = strats

class Tokens(Base):
    __tablename__ = "tokens"
    client = Column(String, primary_key=True)
    auth_token = Column(String)
    auth_token_end = Column(Integer)
    session_token = Column(String)
    session_token_end = Column(Integer)

    def __init__(self, client, auth_token, auth_token_end, session_token, session_token_end):
        self.client = client
        self.auth_token = auth_token
        self.auth_token_end = auth_token_end
        self.session_token = session_token
        self.session_token_end = session_token_end

Base.metadata.create_all(ENGINE)
