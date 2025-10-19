
import numpy as np
import json

class Scaler:
    """
    Simple z-score scaler (mean/std) with save/load.
    """
    def __init__(self):
        self.mean_ = None
        self.std_ = None

    def fit(self, X: np.ndarray):
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0) + 1e-8
        return self

    def transform(self, X: np.ndarray):
        return (X - self.mean_) / self.std_

    def inverse_transform(self, Xn: np.ndarray):
        return Xn * self.std_ + self.mean_

    def save(self, path: str):
        d = {"mean": self.mean_.tolist(), "std": self.std_.tolist()}
        with open(path, "w") as f:
            json.dump(d, f)

    @classmethod
    def load(cls, path: str):
        with open(path, "r") as f:
            d = json.load(f)
        s = cls()
        s.mean_ = np.array(d["mean"], dtype=np.float32)
        s.std_ = np.array(d["std"], dtype=np.float32)
        return s
