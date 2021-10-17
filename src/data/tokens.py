import os
import sys

from sqlalchemy import update

import basilisk_data as bd

THISDIR = os.path.dirname(os.path.abspath(__file__))
BASEDIR = os.path.join(THISDIR, "..", "..")

class Tokens:
    @staticmethod
    def get(client_id):
        with bd.db_session() as db:
            obj = db.query(bd.Tokens).filter(bd.Tokens.client == client_id).one()
        return obj

    @staticmethod
    def update(client_id, new_values):
        with bd.db_session() as db:
            try:
                update_stmt = (
                    update(bd.Tokens.__table__)
                    .where(bd.Tokens.client == client_id)
                    .values(**new_values)
                )
                result = db.execute(update_stmt)
                if result.rowcount == 0:
                    print("Failed to update db.")
                    return False
            except:
                print("Failed to update db.")
                return False
        return True

if __name__ == "__main__":
    pass
