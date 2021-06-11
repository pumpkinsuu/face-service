import numpy as np
from PIL import Image
from base64 import b64decode
from io import BytesIO


def mean(arr):
    return np.mean(arr, 0).tolist()


def l2_normalize(x, axis=-1, epsilon=1e-10):
    output = x / np.sqrt(np.maximum(np.sum(np.square(x), axis=axis, keepdims=True), epsilon))
    return output


def b64ToArray(b64str, size):
    img = Image.open(BytesIO(b64decode(b64str)))\
        .convert('RGB')\
        .resize(size, Image.ANTIALIAS)
    return np.array(img, dtype='uint8')
