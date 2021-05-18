from flask import Flask
from flask_cors import CORS

from config import *

from routes.face import create_face_bp
from utilities import ErrorAPI, response

app = Flask(__name__)
CORS(app)


@app.errorhandler(ErrorAPI)
def error_api(e: ErrorAPI):
    return e.detail()


@app.route('/', methods=['GET'])
def root():
    return response(200, 'ok')


face_bp = create_face_bp(app)
CORS(face_bp)
app.register_blueprint(face_bp)


if __name__ == '__main__':
    app.run(host=HOST, port=PORT)
