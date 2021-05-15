class Model:
    name: str
    input: tuple
    output: int
    tol: float

    def preprocess(self, b64str: str) -> list:
        pass

    def embedding(self, data: list) -> list:
        pass
