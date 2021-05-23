from redis import StrictRedis
from time import sleep
import json
import numpy as np

from config import *

from utilities import logger


def embed_service():
    if MODEL == 'facenet':
        from model.facenet import Model
        model = Model()
    else:
        from model.dlib import Model
        model = Model()

    db = StrictRedis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_EMBED_DB
    )
    db.flushall()
    log = logger('sv_embed.py')

    while True:
        try:
            queue = db.lrange(EMBED_INPUT, 0, EMBED_SIZE - 1)
            ids = []
            inputs = []

            for q in queue:
                data = json.loads(q)
                ids.append(data['id'])
                inputs.append(np.array(data['image'], dtype='uint8'))

            if ids:
                embeds = model.embedding(inputs)

                for idx, embed in zip(ids, embeds):
                    print(len(embed))
                    db.set(idx, json.dumps(embed))

                db.ltrim(EMBED_INPUT, len(ids), - 1)
            else:
                sleep(EMBED_SLEEP)

        except Exception as ex:
            print(ex)
            log.info(ex, exc_info=True)


if __name__ == "__main__":
    embed_service()
