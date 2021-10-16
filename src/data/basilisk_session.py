import os
import sys

THISDIR = os.path.dirname(os.path.abspath(__file__))
BASEDIR = os.path.join(THISDIR, "..", "..")

import basilisk_data as bd

class BasiliskSession:
    @staticmethod
    def get(session_id):
        with bd.db_session() as db:
            obj = db.query(bd.BasiliskSession).filter(bd.BasiliskSession.id == session_id).one()
        return obj
