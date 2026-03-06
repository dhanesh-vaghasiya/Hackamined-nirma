from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass
class EmbeddingBackend:
    name: str
    model: object


class RoleEmbedder:
    def __init__(self) -> None:
        self.backend: EmbeddingBackend | None = None

    def fit(self, texts: List[str]) -> None:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        # Warmup on role texts once.
        _ = model.encode(texts, show_progress_bar=False)
        self.backend = EmbeddingBackend(name="sentence-transformers/all-MiniLM-L6-v2", model=model)

    def encode(self, texts: List[str]) -> np.ndarray:
        if self.backend is None:
            raise RuntimeError("RoleEmbedder is not fitted")

        vectors = self.backend.model.encode(texts, show_progress_bar=False)
        return np.asarray(vectors, dtype=float)


def build_transition_classifier(random_state: int = 42):
    from lightgbm import LGBMClassifier

    return LGBMClassifier(
        n_estimators=250,
        learning_rate=0.05,
        num_leaves=31,
        random_state=random_state,
    ), "lightgbm.LGBMClassifier"


def build_ranker(random_state: int = 42):
    from lightgbm import LGBMRegressor

    return LGBMRegressor(
        n_estimators=350,
        learning_rate=0.04,
        num_leaves=31,
        random_state=random_state,
    ), "lightgbm.LGBMRegressor"


def cosine_similarity_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = np.linalg.norm(a, axis=1, keepdims=True) + 1e-9
    b_norm = np.linalg.norm(b, axis=1, keepdims=True) + 1e-9
    return (a @ b.T) / (a_norm @ b_norm.T)
