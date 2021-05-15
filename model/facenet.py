import tensorflow as tf
from utilities import b64ToArray
import numpy as np

NAME = 'facenet'
INPUT = (160, 160)
OUTPUT = 512
TOL = 0.7
MODEL_PATH = 'model/data/facenet.pb'


def prewhiten(x):
    mean = np.mean(x)
    std = np.std(x)
    std_adj = np.maximum(std, 1.0 / np.sqrt(x.size))
    y = np.multiply(np.subtract(x, mean), 1 / std_adj)
    return y


def l2_normalize(x, axis=-1, epsilon=1e-10):
    output = x / np.sqrt(np.maximum(np.sum(np.square(x), axis=axis, keepdims=True), epsilon))
    return output


def load_pb(path):
    with tf.compat.v1.gfile.GFile(path, "rb") as f:
        graph_def = tf.compat.v1.GraphDef()
        graph_def.ParseFromString(f.read())
    with tf.Graph().as_default() as graph:
        tf.import_graph_def(graph_def, name='')
        return graph


def preprocess(b64str: str):
    return prewhiten(b64ToArray(b64str, INPUT)).tolist()


class Model:
    def __init__(self):
        self.name = NAME
        self.input = INPUT
        self.output = OUTPUT
        self.tol = TOL
        self.graph = load_pb(MODEL_PATH)
        self.sess = tf.compat.v1.Session(graph=self.graph)
        self.tf_input = self.graph.get_tensor_by_name('input:0')
        self.tf_output = self.graph.get_tensor_by_name('embeddings:0')
        self.tf_placeholder = self.graph.get_tensor_by_name('phase_train:0')

    def embedding(self, data: list):
        feed_dict = {self.tf_input: data, self.tf_placeholder: False}

        embeds = self.sess.run(self.tf_output, feed_dict=feed_dict)
        return l2_normalize(embeds).tolist()
