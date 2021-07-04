from flask import Flask, request, g
from flask_cors import CORS
from time import time

from config.server import *

from routes.face import create_face_bp
from database.admin import AdminData
from utilities.api import ErrorAPI, response, logger
log = logger()

app = Flask(__name__)
CORS(app)
admin_db = AdminData(app)


@app.errorhandler(ErrorAPI)
def error_api(e: ErrorAPI):
    return e.detail()


@app.errorhandler(404)
def page_not_found(e):
    return response(404, str(e))


@app.errorhandler(Exception)
def exception(e):
    log.exception(e)
    return response(500, 'internal server error')


@app.before_request
def check_request():
    g.start = time()

    if 'Authorization' not in request.headers:
        raise ErrorAPI(400, 'no api_key provided')
    api_key = request.headers['Authorization']

    data = admin_db.get_data({'key': api_key})
    if not data:
        raise ErrorAPI(401, 'invalid api_key')
    g.collection = data['collection']


@app.route('/', methods=['GET'])
def root():
    return response(200, 'ok')


face_bp = create_face_bp(app)
CORS(face_bp)
app.register_blueprint(face_bp)


if __name__ == '__main__':
    app.run(host=HOST, port=PORT)
