from flask import Flask
from flask_cors import CORS

import config

from router.face import create_face_bp
from utilities import ErrorAPI

app = Flask(__name__)
CORS(app)


@app.errorhandler(ErrorAPI)
def error_api(e: ErrorAPI):
    return e.detail()


@app.route('/', methods=['GET'])
def root():
    return 'ok', 200


def main():
    face_bp = create_face_bp(app)
    CORS(face_bp)
    app.register_blueprint(face_bp)

    app.run(host=config.HOST, port=config.PORT)


if __name__ == '__main__':
    main()
