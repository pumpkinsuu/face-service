from flask import request, Blueprint
from uuid import uuid4
import json
from time import sleep
from redis import StrictRedis

import config

from database.mongo import Database
from utilities import *


def create_face_bp(app):
    face_bp = Blueprint('face_bp', __name__)

    if config.MODEL == 'dlib':
        from model.dlib import preprocess, NAME, OUTPUT, TOL
    else:
        from model.facenet import preprocess, NAME, OUTPUT, TOL

    face_db = Database(NAME, OUTPUT, app)

    embed_db = StrictRedis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_EMBED_DB
    )
    update_db = StrictRedis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_UPDATE_DB
    )

    def get_embed(images):
        data = {}
        i = ''
        for img in images:
            i = str(uuid4())
            data[i] = []
            req = {
                'id': i,
                'image': preprocess(img)
            }
            embed_db.rpush(config.EMBED_INPUT, json.dumps(req))

        while True:
            if embed_db.get(i):
                for x in data:
                    embed = embed_db.get(x)
                    data[x] = np.array(json.loads(embed))
                    embed_db.delete(x)

                return list(data.values())

            sleep(config.REQUEST_SLEEP)

    def update(collection, user, new):
        req = {
            'id': str(uuid4()),
            'collection': collection,
            'user': user,
            'new': new
        }
        update_db.rpush(config.UPDATE_INPUT, json.dumps(req))

        while True:
            res = update_db.get(req['id'])

            if res:
                update_db.delete(req['id'])
                return int(res)

            sleep(config.REQUEST_SLEEP)

    @face_bp.route('/<collection>/users/<user_id>', methods=['GET'])
    def get_user(collection: str, user_id: str):
        user = face_db.get_user(collection, user_id)
        if not user:
            raise ErrorAPI(404, 'user not found')

        return response(200, 'exist')

    @face_bp.route('/<collection>/users', methods=['GET'])
    def get_users(collection: str):
        ids, _ = face_db.get_users(collection)
        return response(200, ids)

    @face_bp.route('/<collection>/users/<user_id>', methods=['POST', 'PUT'])
    def update_user(collection: str, user_id: str):
        if 'front' not in request.form:
            raise ErrorAPI(400, 'missing "front"')
        if 'left' not in request.form:
            raise ErrorAPI(400, 'missing "left"')
        if 'right' not in request.form:
            raise ErrorAPI(400, 'missing "right"')

        f, l, r = get_embed([
            request.form['front'],
            request.form['left'],
            request.form['right']
        ])

        if distance(f, l) > TOL or distance(f, r) > TOL:
            raise ErrorAPI(400, 'different person')

        user = {
            'id': user_id,
            'embed': mean([f, l, r])
        }

        if request.method == 'POST':
            if face_db.get_user(collection, user_id):
                raise ErrorAPI(409, 'user already exists')
            status = update(
                collection=collection,
                user=user,
                new=True
            )
        else:
            if not face_db.get_user(collection, user_id):
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

    @face_bp.route('/<collection>/users/<user_id>', methods=['DELETE'])
    def remove_user(collection: str, user_id: str):
        if not face_db.get_user(collection, user_id):
            raise ErrorAPI(404, 'user not registered')

        if not face_db.remove(collection, user_id):
            raise ErrorAPI(500, 'failed')

        return {'result': 'success'}

    @face_bp.route('/<collection>/verify', methods=['POST'])
    def verify(collection: str):
        if 'images' not in request.form:
            raise ErrorAPI(400, 'missing "images"')

        images = request.form.getlist('images')
        if not isinstance(images, list):
            raise ErrorAPI(400, '"images" not list')

        if face_db.count(collection) < 1:
            raise ErrorAPI(500, 'database empty')

        db_ids, db_embeds = face_db.get_users(collection)
        embeds = get_embed(images)
        ids = []

        for embed in embeds:
            idx, dist = find_min(embed, db_embeds)

            if dist < TOL:
                ids.append(db_ids[idx])
            else:
                ids.append('')

        return response(200, ids)

    @face_bp.route('/{collection}', methods=['GET'])
    def count_collection(collection: str):
        return response(200, face_db.count(collection))

    @face_bp.route('/{collection}', methods=['PUT'])
    def rename_collection(collection: str):
        if 'name' not in request.args:
            raise ErrorAPI(400, 'missing "name"')
        if not face_db.rename(collection, request.args['name']):
            raise ErrorAPI(500, 'failed')

        return response(200, 'success')

    @face_bp.route('/<collection>', methods=['DELETE'])
    def drop_collection(collection: str):
        if not face_db.drop(collection):
            raise ErrorAPI(500, 'failed')

        return response(200, 'success')

    return face_bp
