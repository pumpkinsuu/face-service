import numpy as np
from PIL import Image
from base64 import b64decode
from io import BytesIO
import logging
from flask import jsonify


def mean(arr):
    return np.mean(arr, 0).tolist()


def distance(a, b, axis=None):
    return np.sqrt(np.sum((a - b) ** 2, axis))


def find_min(x, arr):
    dist = distance(x, arr, 1)
    idx = np.argmin(dist)
    return idx, dist[idx]


def b64ToArray(b64str, size):
    img = Image.open(BytesIO(b64decode(b64str)))\
        .convert('RGB')\
        .resize(size, Image.ANTIALIAS)
    return np.array(img, dtype='uint8')


def logger(name):
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    file = logging.FileHandler('error.log', mode='w+')
    file.setFormatter(
        logging.Formatter(
            '[%(asctime)s] — <%(name)s>: %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
    )
    log.addHandler(file)
    return log


def response(status, message, data=''):
    return jsonify({
        'status': status,
        'message': message,
        'data': data
    }), status


class ErrorAPI(Exception):
    def __init__(self, status, message):
        super().__init__()
        self.status = status
        self.message = message

    def detail(self):
        return response(self.status, self.message)
