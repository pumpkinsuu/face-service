from pymongo import MongoClient, TEXT, ASCENDING, DESCENDING
from flask_pymongo import PyMongo
import secrets

from config.server import MONGO_URI, USER_DB
from utilities import logger


class AdminData:
    def __init__(self, app=None):
        uri = MONGO_URI + USER_DB
        if app:
            self.db = PyMongo(app, uri=uri).db.db
        else:
            self.db = MongoClient(uri).db

        if self.db.count_documents({}) == 0:
            self.db.create_index([('collection', TEXT), ('key', TEXT)], unique=True)

        self.log = logger('adminDB')

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
            self.log.info(ex, exc_info=True)
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
            self.log.info(ex, exc_info=True)
            return ''

    def remove(self, collection: str):
        try:
            self.db.delete_one({'collection': collection})
            return True
        except Exception as ex:
            self.log.info(ex, exc_info=True)
            return False
