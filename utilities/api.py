import logging
from flask import jsonify


def logger(name):
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    file = logging.FileHandler('../error.log', mode='w+')
    file.setFormatter(
        logging.Formatter(
            '[%(asctime)s] — <%(name)s>: %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
    )
    log.addHandler(file)
    return log


def response(code, data):
    return jsonify(data), code


class ErrorAPI(Exception):
    def __init__(self, code, message):
        super().__init__()
        self.code = code
        self.message = message

    def detail(self):
        return response(
            self.code,
            {
                'error': {
                    'code': self.code,
                    'message': self.message
                }
            }
        )
