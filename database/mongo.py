from pymongo import MongoClient, TEXT
from flask_pymongo import PyMongo
import numpy as np

import config

from utilities import logger


class Database:
    def __init__(self,
                 model_name: str,
                 model_output: int,
                 app=None):
        if app:
            self.db = PyMongo(app, uri=config.MONGO_URI).db
        else:
            self.db = MongoClient(config.MONGO_URI).db

        self.model_name = model_name
        self.model_output = model_output
        self.log = logger('mongo.py')

    def get_user(self,
                 collection: str,
                 user_id: str):
        return self.db[self.model_name + collection].find_one({'id': user_id})

    def get_users(self,
                  collection: str):
        results = self.db[self.model_name + collection].find()
        size = results.count()

        if size == 0:
            return np.array([]), np.array([])

        ids = [None] * size
        embeds = np.empty((size, self.model_output))

        for i in range(size):
            ids[i] = results[i]['id']
            embeds[i] = results[i]['embed']

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
            self.log.info(ex, exc_info=True)
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
                        'embed': user['embed']
                    }
                }
            )

            return True
        except Exception as ex:
            self.log.info(ex, exc_info=True)
            return False

    def remove(self,
               collection: str,
               user_id: str):
        try:
            self.db[self.model_name + collection].delete_one({'id': user_id})
            return True
        except Exception as ex:
            self.log.info(ex, exc_info=True)
            return False

    def count(self,
              collection: str):
        try:
            return self.db[self.model_name + collection].count_documents({})
        except Exception as ex:
            self.log.info(ex, exc_info=True)
            return -1

    def rename(self,
               collection: str,
               name: str):
        try:
            self.db[self.model_name + collection].rename(name)
            return True
        except Exception as ex:
            self.log.info(ex, exc_info=True)
            return False

    def drop(self,
             collection: str):
        try:
            self.db.drop_collection(self.model_name + collection)
            return True
        except Exception as ex:
            self.log.info(ex, exc_info=True)
            return False
