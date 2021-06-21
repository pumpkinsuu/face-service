from pymongo import MongoClient, TEXT
from flask_pymongo import PyMongo
import numpy as np

from config.server import FACE_URI, FACE_DB

from utilities.api import logger


class FaceData:
    def __init__(self,
                 model_name: str,
                 model_output: int,
                 app=None):
        if app:
            self.db = PyMongo(app, uri=FACE_URI).db
        else:
            self.db = MongoClient(FACE_URI)[FACE_DB]

        self.model_name = model_name
        self.model_output = model_output
        self.log = logger()

    def get_user(self,
                 collection: str,
                 user_id: str):
        return self.db[self.model_name + collection].find_one({'id': user_id})

    def get_users(self,
                  collection: str):
        size = self.db[self.model_name + collection].count_documents({})

        if size == 0:
            return [], np.array([])

        results = self.db[self.model_name + collection].find()

        ids = [None] * size
        embeds = np.empty((size, 3, self.model_output))

        for i in range(size):
            ids[i] = results[i]['id']
            embeds[i] = results[i]['embeds']

        return ids, embeds

    def create(self,
               collection: str,
               user: dict):
        try:
            if self.db[self.model_name + collection].count_documents({}) == 0:
                self.db[self.model_name + collection].create_index([('id', TEXT)], unique=True)

            self.db[self.model_name + collection].insert_one(user)

            return True
        except Exception as ex:
            self.log.exception(ex)
            return False

    def update(self,
               collection: str,
               user: dict):
        try:
            self.db[self.model_name + collection].update_one(
                {
                    'id': user['id']
                },
                {
                    "$set": {
                        'embeds': user['embeds']
                    }
                }
            )
            return True
        except Exception as ex:
            self.log.exception(ex)
            return False

    def remove(self,
               collection: str,
               user_id: str):
        self.db[self.model_name + collection].delete_one({'id': user_id})
        return not self.db[self.model_name + collection].find_one({'id': user_id})

    def count(self,
              collection: str):
        return self.db[self.model_name + collection].count_documents({})
