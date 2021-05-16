from redis import StrictRedis
from time import sleep
import json
import numpy as np

import config

from database.mongo import Database
from utilities import logger, find_min


def update_service():
    if config.MODEL == 'facenet':
        from model.facenet import NAME, OUTPUT, TOL
    else:
        from model.dlib import NAME, OUTPUT, TOL

    face_db = Database(NAME, OUTPUT)
    db = StrictRedis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_UPDATE_DB
    )
    db.flushall()
    log = logger('update.py')

    while True:
        try:
            req = db.lpop(config.UPDATE_INPUT)

            if req:
                req = json.loads(req)
                user = req['user']

                ids, embeds = face_db.get_users(req['collection'])

                idx = -1
                dist = 0
                if len(ids):
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
                sleep(config.UPDATE_SLEEP)

        except Exception as ex:
            log.info(ex, exc_info=True)
