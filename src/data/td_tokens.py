import os
import sys

THISDIR = os.path.dirname(os.path.abspath(__file__))
BASEDIR = os.path.join(THISDIR, "..", "..")

import basilisk_data as bd

class TDTokens:
    @staticmethod
    def get():
        with bd.db_session() as bd:
            obj = db.query(bd.TDTokens).one()
        return obj
