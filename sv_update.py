from redis import StrictRedis
from time import sleep
import json
import numpy as np

from config.server import *

from database.face import FaceData
from utilities.api import logger
from utilities.face_method import get_method


def update_service():
    import importlib
    module = importlib.import_module(f'model.{MODEL}')
    Model = getattr(module, 'Model')
    model = Model()

    face_db = FaceData(model.name, model.output)
    db = StrictRedis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_UPDATE_DB
    )
    db.flushall()
    log = logger()
    find_min = get_method()

    while True:
        try:
            req = db.lpop(UPDATE_INPUT)

            if req:
                req = json.loads(req)
                user = req['user']
                embeds = np.array(user['embeds'])

                db_ids, db_embeds = face_db.get_users(req['collection'])

                if db_ids:
                    dist, ids = find_min(embeds, db_embeds, METRIC)
                    exist = np.any(np.array(db_ids)[ids[dist < model.tol]] != user['id'])
                else:
                    exist = False

                code = 500
                if exist:
                    code = 409
                elif req['new']:
                    if face_db.create(
                        req['collection'],
                        user
                    ):
                        code = 201
                else:
                    if face_db.update(
                        req['collection'],
                        user
                    ):
                        code = 200

                db.set(req['id'], code)
            else:
                sleep(UPDATE_SLEEP)

        except Exception as ex:
            log.exception(ex)
            db.flushall()


if __name__ == "__main__":
    update_service()
