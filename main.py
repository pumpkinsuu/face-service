from flask import Flask, request, g
from flask_cors import CORS

from config.server import *

from routes.face import create_face_bp
from database.admin import AdminData
from utilities import ErrorAPI, response, logger
log = logger('face')

app = Flask(__name__)
CORS(app)
admin_db = AdminData(app)


@app.errorhandler(ErrorAPI)
def error_api(e: ErrorAPI):
    return e.detail()


@app.errorhandler(Exception)
def exception(e):
    log.info(str(e), exc_info=True)
    return response(500, str(e))


@app.before_request
def check_request():
    if 'api_key' not in request.headers:
        raise ErrorAPI(400, 'no api_key provided')
    api_key = request.headers['api_key']

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
