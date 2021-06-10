from flask import request, Blueprint, g
from uuid import uuid4
import json
from time import sleep
from redis import StrictRedis

from config.server import *

from database.face import FaceData
from utilities import *
log = logger('face.py')


def create_face_bp(app):
    face_bp = Blueprint('face_bp', __name__)

    if MODEL == 'dlib':
        from model.dlib import preprocess, NAME, OUTPUT, TOL
    else:
        from model.facenet import preprocess, NAME, OUTPUT, TOL

    face_db = FaceData(NAME, OUTPUT, app)

    embed_db = StrictRedis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_EMBED_DB
    )
    update_db = StrictRedis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_UPDATE_DB
    )

    def get_embed(images):
        data = {}
        i = ''
        for img in images:
            if not img:
                raise ErrorAPI(400, 'image empty')

            i = str(uuid4())
            data[i] = []
            req = {
                'id': i,
                'image': preprocess(img)
            }
            embed_db.rpush(EMBED_INPUT, json.dumps(req))

        t = 0
        while t < TIMEOUT:
            try:
                if embed_db.get(i):
                    for x in data:
                        embed = embed_db.get(x)
                        data[x] = np.array(json.loads(embed))
                        embed_db.delete(x)

                    return list(data.values())

                sleep(REQUEST_SLEEP)
                t += REQUEST_SLEEP
            except Exception as ex:
                for x in data:
                    embed_db.delete(x)

                log.info(str(ex), exc_info=True)
                raise ErrorAPI(500, str(ex))

    def update(collection, user, new):
        req = {
            'id': str(uuid4()),
            'collection': collection,
            'user': user,
            'new': new
        }
        update_db.rpush(UPDATE_INPUT, json.dumps(req))

        t = 0
        while t < TIMEOUT:
            res = update_db.get(req['id'])

            if res:
                update_db.delete(req['id'])
                return int(res)

            sleep(REQUEST_SLEEP)
            t += REQUEST_SLEEP

    @face_bp.route('/users/<userID>', methods=['GET'])
    def get_user(userID: str):
        user = face_db.get_user(
            g['collection'],
            userID
        )
        if not user:
            raise ErrorAPI(404, 'user not found')

        return response(200, 'exist')

    @face_bp.route('/count', methods=['GET'])
    def count():
        total = face_db.count(g['collection'])
        return response(200, total)

    @face_bp.route('/users', methods=['GET'])
    def get_users():
        ids, _ = face_db.get_users(g['collection'])
        return response(200, ids)

    @face_bp.route('/users/<userID>', methods=['POST', 'PUT'])
    def update_user(userID: str):
        if 'front' not in request.form:
            raise ErrorAPI(400, 'missing "front"')
        if 'left' not in request.form:
            raise ErrorAPI(400, 'missing "left"')
        if 'right' not in request.form:
            raise ErrorAPI(400, 'missing "right"')

        collection = g['collection']

        front = request.form['front']
        left = request.form['left']
        right = request.form['right']

        front, left, right = get_embed([front, left, right])

        if distance(front, left) > TOL or distance(front, right) > TOL:
            raise ErrorAPI(400, 'different person')

        user = {
            'id': userID,
            'embed': mean([front, left, right])
        }

        if request.method == 'POST':
            if face_db.get_user(collection, userID):
                raise ErrorAPI(409, 'user already exists')
            status = update(
                collection=collection,
                user=user,
                new=True
            )
        else:
            if not face_db.get_user(collection, userID):
                raise ErrorAPI(404, 'user not registered')
            status = update(
                collection=collection,
                user=user,
                new=False
            )

        if status == 409:
            raise ErrorAPI(409, 'face already exists')

        if status == 500:
            raise ErrorAPI(500, 'failed')

        return response(status, 'success')

    @face_bp.route('/users/<userID>', methods=['DELETE'])
    def remove_user(userID: str):
        collection = g['collection']

        if not face_db.get_user(collection, userID):
            raise ErrorAPI(404, 'user not registered')

        if not face_db.remove(collection, userID):
            raise ErrorAPI(500, 'failed')

        return response(200, 'success')

    @face_bp.route('/find', methods=['POST'])
    def find():
        collection = g['collection']

        if 'images' not in request.form:
            raise ErrorAPI(400, 'missing "images"')

        images = request.form.getlist('images')
        if not isinstance(images, list):
            raise ErrorAPI(400, '"images" not list')

        db_ids, db_embeds = face_db.get_users(collection)
        if not db_ids:
            raise ErrorAPI(500, 'no face registered')

        embeds = get_embed(images)
        ids = []

        for embed in embeds:
            idx, dist = find_min(embed, db_embeds)

            if dist < TOL:
                ids.append(db_ids[idx])
            else:
                ids.append('')

        return response(200, ids)

    return face_bp
