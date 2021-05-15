from redis import StrictRedis
from time import sleep
import json
import numpy as np

import config

from utilities import logger


def main():
    if config.MODEL == 'facenet':
        from model.facenet import Model
        model = Model()
    else:
        from model.dlib import Model
        model = Model()

    db = StrictRedis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_EMBED_DB
    )
    db.flushall()
    log = logger('sv_embed.py')

    while True:
        try:
            queue = db.lrange(config.EMBED_INPUT, 0, config.EMBED_SIZE - 1)
            ids = []
            inputs = []

            for q in queue:
                data = json.loads(q)
                ids.append(data['id'])
                inputs.append(np.array(data['image'], dtype='uint8'))

            if ids:
                embeds = model.embedding(inputs)

                for idx, embed in zip(ids, embeds):
                    db.set(idx, json.dumps(embed))

                db.ltrim(config.EMBED_INPUT, len(ids), - 1)
            else:
                sleep(config.EMBED_SLEEP)

        except Exception as ex:
            print(ex)
            log.info(ex, exc_info=True)


if __name__ == '__main__':
    main()
