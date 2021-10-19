import os
import sys

import basilisk_data as bd

THISDIR = os.path.dirname(os.path.abspath(__file__))
BASEDIR = os.path.join(THISDIR, "..", "..")

class SessionEndpoint:
    @staticmethod
    def get(session_id):
        with bd.db_session() as db:
            obj = db.query(bd.BasiliskSession).filter(bd.BasiliskSession.id == session_id).one()
        return obj

    @staticmethod
    def update(session_id, new_values):
        with bd.db_session() as db:
            try:
                update_stmt = (
                    update(bd.BasiliskSession.__table__)
                    .where(bd.BasiliskSession.session_id == session_id)
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

    @staticmethod
    def insert(body):
        with bd.db_session() as db:
            try:
                session = bd.BasiliskSession(
                    int(body["session_id"]),
                    body["clients"],
                    body["strats"]
                )
                db.add(session)
            except Exception as e:
                print(f"Failed to update db. Exception: {e}")
                return False
        return True

if __name__ == "__main__":
    pass
