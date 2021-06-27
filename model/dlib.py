import face_recognition as fr
from utilities.face import b64ToArray, l2_normalize
from config.server import METRIC

NAME = 'dlib'
INPUT = (150, 150)
OUTPUT = 128
if METRIC == 'cosine':
    TOL = 0.03
else:
    TOL = 0.25
FACE_LOCATION = [(0, 150, 150, 0)]


def preprocess(b64str: str):
    return b64ToArray(b64str, INPUT).tolist()


class Model:
    def __init__(self):
        self.model = fr
        self.name = NAME
        self.input = INPUT
        self.output = OUTPUT
        self.tol = TOL
        self.face_location = FACE_LOCATION

    def embedding(self, data: list):
        embeds = [
            self.model.face_encodings(img, self.face_location)[0].tolist()
            for img in data
        ]
        return l2_normalize(embeds).tolist()
