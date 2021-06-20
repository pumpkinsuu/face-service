from flask import request, Blueprint, g
from uuid import uuid4
import json
from time import sleep, time
from redis import StrictRedis
from scipy.spatial.distance import cdist
import numpy as np

from config.server import *

from database.face import FaceData
from utilities.api import logger, ErrorAPI, response
from utilities.face_method import get_method


def create_face_bp(app):
    face_bp = Blueprint('face_bp', __name__)

    if MODEL == 'dlib':
        from model.dlib import preprocess, NAME, OUTPUT, TOL
    else:
        from model.facenet import preprocess, NAME, OUTPUT, TOL

    log = logger()
    find_min = get_method()

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
            i = str(uuid4())
            data[i] = []
            req = {
                'id': i,
                'image': preprocess(img)
            }
            embed_db.rpush(EMBED_INPUT, json.dumps(req))

        try:
            t = 0
            while t < TIMEOUT:
                if embed_db.get(i):
                    for x in data:
                        embed = embed_db.get(x)
                        data[x] = json.loads(embed)
                        embed_db.delete(x)

                    return list(data.values())

                sleep(REQUEST_SLEEP)
                t += REQUEST_SLEEP

            raise Exception('embedding timeout')
        except Exception as ex:
            for x in data:
                embed_db.delete(x)

            log.exception(ex)
            raise ErrorAPI(500, ex)

    def update(collection, user, new):
        req = {
            'id': str(uuid4()),
            'collection': collection,
            'user': user,
            'new': new
        }
        update_db.rpush(UPDATE_INPUT, json.dumps(req))

        try:
            t = 0
            while t < TIMEOUT:
                res = update_db.get(req['id'])

                if res:
                    update_db.delete(req['id'])
                    return int(res)

                sleep(REQUEST_SLEEP)
                t += REQUEST_SLEEP

            raise Exception('updating timeout')
        except Exception as ex:
            update_db.delete(req['id'])

            log.exception(ex)
            raise ErrorAPI(500, ex)

    @face_bp.route('/users/<userID>', methods=['GET'])
    def get_user(userID: str):
        user = face_db.get_user(
            g.collection,
            userID
        )
        return response(200, {'status': bool(user)})

    @face_bp.route('/count', methods=['GET'])
    def count():
        total = face_db.count(g.collection)
        return response(200, {'total': total})

    @face_bp.route('/users', methods=['GET'])
    def get_users():
        ids, _ = face_db.get_users(g.collection)
        return response(200, {'users': ids})

    @face_bp.route('/users/<userID>', methods=['POST', 'PUT'])
    def update_user(userID: str):
        front = request.form.get('front')
        if not front:
            raise ErrorAPI(400, 'missing front')
        left = request.form.get('left')
        if not left:
            raise ErrorAPI(400, 'missing left')
        right = request.form.get('right')
        if not right:
            raise ErrorAPI(400, 'missing right')

        collection = g.collection
        check_t = time()

        front, left, right = get_embed([front, left, right])
        embed_t = time()

        dist = cdist(
            np.array([front]),
            np.array([left, right]),
            METRIC
        ).max()
        if dist > TOL:
            raise ErrorAPI(400, 'different person')

        user = {
            'id': userID,
            'embeds': [front, left, right]
        }

        if request.method == 'POST':
            if face_db.get_user(collection, userID):
                raise ErrorAPI(409, 'user already exists')
            status = update(
                collection=collection,
                user=user,
                new=True
            )
            msg = 'created'
        else:
            if not face_db.get_user(collection, userID):
                raise ErrorAPI(404, 'user not registered')
            status = update(
                collection=collection,
                user=user,
                new=False
            )
            msg = 'updated'

        if status == 409:
            raise ErrorAPI(409, 'face already exists')
        if status == 500:
            raise ErrorAPI(500, 'failed')

        data = {
            'status': msg,
            'valid': check_t - g.start,
            'embed': embed_t - check_t,
            'update': time() - embed_t,
            'total': time() - g.start
        }
        return response(status, data)

    @face_bp.route('/users/<userID>', methods=['DELETE'])
    def remove_user(userID: str):
        collection = g.collection

        if not face_db.get_user(collection, userID):
            raise ErrorAPI(404, 'user not registered')

        if not face_db.remove(collection, userID):
            raise ErrorAPI(500, 'failed')

        return response(200, {'status': 'removed'})

    @face_bp.route('/find', methods=['POST'])
    def find():
        collection = g.collection

        images = request.form.getlist('images')
        if not images:
            raise ErrorAPI(400, 'missing images')
        if not isinstance(images, list):
            raise ErrorAPI(400, 'images not list')

        db_ids, db_embeds = face_db.get_users(collection)
        if not db_ids:
            raise ErrorAPI(400, 'no face registered')
        check_t = time()

        embeds = get_embed(images)
        embed_t = time()

        dist, ids = find_min(embeds, db_embeds, METRIC)
        users = np.array(db_ids)[ids]
        users[dist >= TOL] = ''

        data = {
            'users': users.tolist(),
            'valid': check_t - g.start,
            'embed': embed_t - check_t,
            'search': time() - embed_t,
            'total': time() - g.start
        }
        return response(200, data)

    @face_bp.route('/verify', methods=['POST'])
    def verify():
        collection = g.collection

        userID = request.form.get('userID')
        if not userID:
            raise ErrorAPI(400, 'missing userID')

        user = face_db.get_user(collection, userID)
        if not user:
            raise ErrorAPI(404, 'user not exist')

        images = request.form.getlist('images')
        if not images:
            raise ErrorAPI(400, 'missing images')
        if not isinstance(images, list):
            raise ErrorAPI(400, 'images not list')

        embeds = get_embed(images)
        dist, _ = find_min(embeds, np.array([user['embeds']]), METRIC)
        result = np.all(dist < TOL)

        return response(200, {'result': bool(result)})

    return face_bp
