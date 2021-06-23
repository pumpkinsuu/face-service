# Model
MODELS = ['dlib', 'facenet']
MODEL = 'dlib'
"""
    euclidean
    cosine
"""
METRIC = 'euclidean'
"""
    mean_first
    mean_later
    min_later
"""
METHOD = 'mean_first'
# Server
HOST = '0.0.0.0'
PORT = 5001
TIMEOUT = 5
# Redis
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
REDIS_EMBED_DB = 0
REDIS_UPDATE_DB = 1
REQUEST_SLEEP = 0.1
# Model
EMBED_INPUT = 'images'
EMBED_SIZE = 3
EMBED_SLEEP = 0.1
# Register
UPDATE_INPUT = 'users'
UPDATE_SLEEP = 0.1
# Mongo
MONGO_URI = f"mongodb+srv://admin:AdminPass123" \
            f"@cluster0.qe6sa.mongodb.net/"
FACE_DB = 'face_db'
FACE_URI = MONGO_URI + FACE_DB + "?retryWrites=true&w=majority"
USER_DB = 'user_db'
