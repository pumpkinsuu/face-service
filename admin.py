from flask import Flask, session
from flask_cors import CORS
from datetime import timedelta

from config.admin import *

from routes.admin import create_admin_bp
from utilities.api import ErrorAPI, logger, response
log = logger()

app = Flask(__name__)
CORS(app)
app.secret_key = SECRET


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
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=1)


admin_bp = create_admin_bp(app)
CORS(admin_bp)
app.register_blueprint(admin_bp)


if __name__ == '__main__':
    app.run(host=HOST, port=PORT)
