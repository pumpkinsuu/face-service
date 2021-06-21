from pymongo import TEXT, ASCENDING
from flask_pymongo import PyMongo
import secrets

from config.server import MONGO_URI, USER_DB, FACE_DB, MODELS
from utilities.api import logger


class AdminData:
    def __init__(self, app):
        self.db = PyMongo(app, uri=MONGO_URI + USER_DB).db.db
        self.face_db = PyMongo(app, uri=MONGO_URI + FACE_DB).db

        if self.db.count_documents({}) == 0:
            self.db.create_index([('collection', TEXT), ('key', TEXT)], unique=True)

        self.log = logger()

    def get_data(self, data: dict):
        return self.db.find_one(data)

    def get(self):
        results = self.db.find().sort([("collection", ASCENDING)])
        return list(results)

    def search(self, keyword):
        results = self.db.find(
            {"$text": {"$search": keyword}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})])
        return list(results)

    def create(self, collection: str):
        try:
            key = secrets.token_urlsafe()
            while self.db.find_one({'key': key}):
                key = secrets.token_urlsafe()

            self.db.insert_one({
                'collection': collection,
                'key': key
            })
            return key
        except Exception as ex:
            self.log.exception(ex)
            return ''

    def update(self, collection: str):
        try:
            key = secrets.token_urlsafe()
            while self.db.find_one({'key': key}):
                key = secrets.token_urlsafe()

            self.db.update_one(
                {
                    'collection': collection
                },
                {
                    "$set": {
                        'key': key
                    }
                }
            )
            return key
        except Exception as ex:
            self.log.exception(ex)
            return ''

    def remove(self, collection: str):
        data = {'collection': collection}
        for model in MODELS:
            self.face_db.drop_collection(model + collection)

        self.db.delete_one(data)

        return not self.db.find_one(data)
