# Model
"""
    facenet
    dlib
"""
MODEL = 'dlib'
# Server
HOST = '0.0.0.0'
PORT = 5001
# Redis
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
REDIS_EMBED_DB = 0
REDIS_UPDATE_DB = 1
REQUEST_SLEEP = 0.1
# Model
EMBED_INPUT = 'images'
EMBED_SIZE = 30
EMBED_SLEEP = 0.1
# Register
UPDATE_INPUT = 'users'
UPDATE_SLEEP = 0.1
# Mongo
MONGO_DB = 'face_db'
MONGO_URI = f"mongodb+srv://admin:AdminPass123" \
            f"@cluster0.qe6sa.mongodb.net/{MONGO_DB}" \
            f"?retryWrites=true&w=majority"
