# Model
"""
    facenet
    dlib
"""
MODEL = 'dlib'
# Server
HOST = 'localhost'
PORT = 5001
ORIGINS = [
    f'http://{HOST}',
    f'http://{HOST}:{PORT}',
]
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
MONGO_URI = f"mongodb+srv://admin:AdminPass123" \
            f"@cluster0.qe6sa.mongodb.net/face_db" \
            f"?retryWrites=true&w=majority"
