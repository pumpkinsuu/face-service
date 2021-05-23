from redis import StrictRedis
from time import sleep
import json
import numpy as np

from config import *

from database.mongo import Database
from utilities import logger, find_min


def update_service():
    if MODEL == 'facenet':
        from model.facenet import NAME, OUTPUT, TOL
    else:
        from model.dlib import NAME, OUTPUT, TOL

    face_db = Database(NAME, OUTPUT)
    db = StrictRedis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_UPDATE_DB
    )
    db.flushall()
    log = logger('sv_update.py')

    while True:
        try:
            req = db.lpop(UPDATE_INPUT)

            if req:
                req = json.loads(req)
                user = req['user']

                ids, embeds = face_db.get_users(req['collection'])

                idx = -1
                dist = 0
                if ids:
                    idx, dist = find_min(np.array(user['embed']), embeds)

                code = 409
                if req['new']:
                    if idx == -1 or dist > TOL:
                        code = 500
                        if face_db.create(
                                req['collection'],
                                user
                        ):
                            code = 201
                elif idx != -1:
                    if dist > TOL or ids[idx] == user['id']:
                        code = 500
                        if face_db.update(
                            req['collection'],
                            user
                        ):
                            code = 200

                db.set(req['id'], code)
            else:
                sleep(UPDATE_SLEEP)

        except Exception as ex:
            log.info(ex, exc_info=True)


if __name__ == "__main__":
    update_service()
