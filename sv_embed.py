from redis import StrictRedis
from time import sleep
import json
import numpy as np

from config.server import *

from utilities.api import logger


def embed_service():
    import importlib
    module = importlib.import_module(f'model.{MODEL}')
    Model = getattr(module, 'Model')
    model = Model()
    model.load()

    db = StrictRedis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_EMBED_DB
    )
    db.flushall()
    log = logger()

    while True:
        try:
            queue = db.lrange(EMBED_INPUT, 0, EMBED_SIZE - 1)
            ids = []
            inputs = []

            for q in queue:
                data = json.loads(q)
                ids.append(data['id'])
                inputs.append(np.array(data['image']))

            if ids:
                embeds = model.embedding(inputs)

                for idx, embed in zip(ids, embeds):
                    db.set(idx, json.dumps(embed))

                db.ltrim(EMBED_INPUT, len(ids), - 1)
            else:
                sleep(EMBED_SLEEP)

        except Exception as ex:
            log.exception(ex)
            db.flushall()


if __name__ == "__main__":
    embed_service()
