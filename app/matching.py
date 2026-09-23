"""Motor de matching semántico lead <-> propiedades.

Dos implementaciones intercambiables (Strategy pattern):

- TfidfMatcher: scikit-learn TfidfVectorizer + cosine_similarity. Default:
  instantáneo, sin dependencias pesadas, determinístico -> ideal para tests y CI.
- EmbeddingMatcher: sentence-transformers (import perezoso, opcional). Mismo
  contrato, mejor calidad semántica, pero requiere descargar un modelo.

Se elige con la env var EMBEDDING_ENGINE (ver app/config.py).
"""
from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models import Property, PropertyMatch


@dataclass
class Matcher:
    properties: list[Property]

    def top_matches(self, query: str, k: int = 3) -> list[PropertyMatch]:
        raise NotImplementedError


@dataclass
class TfidfMatcher(Matcher):
    def __post_init__(self) -> None:
        corpus = [f"{p.title} {p.description} {p.neighborhood}" for p in self.properties]
        self._vectorizer = TfidfVectorizer(stop_words=None)
        self._matrix = self._vectorizer.fit_transform(corpus) if corpus else None

    def top_matches(self, query: str, k: int = 3) -> list[PropertyMatch]:
        if not self.properties or self._matrix is None:
            return []
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]
        ranked = sorted(zip(self.properties, scores), key=lambda pair: pair[1], reverse=True)
        return [
            PropertyMatch(property_id=p.id, title=p.title, score=round(float(score), 4))
            for p, score in ranked[:k]
        ]


@dataclass
class EmbeddingMatcher(Matcher):
    """Requiere `pip install sentence-transformers` (comentado en requirements.txt)."""

    _MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __post_init__(self) -> None:
        from sentence_transformers import SentenceTransformer  # import perezoso

        self._model = SentenceTransformer(self._MODEL_NAME)
        corpus = [f"{p.title} {p.description} {p.neighborhood}" for p in self.properties]
        self._embeddings = self._model.encode(corpus) if corpus else None

    def top_matches(self, query: str, k: int = 3) -> list[PropertyMatch]:
        if not self.properties or self._embeddings is None:
            return []
        query_vec = self._model.encode([query])
        scores = cosine_similarity(query_vec, self._embeddings)[0]
        ranked = sorted(zip(self.properties, scores), key=lambda pair: pair[1], reverse=True)
        return [
            PropertyMatch(property_id=p.id, title=p.title, score=round(float(score), 4))
            for p, score in ranked[:k]
        ]


def build_matcher(properties: list[Property], engine: str = "tfidf") -> Matcher:
    if engine == "sentence-transformers":
        return EmbeddingMatcher(properties)
    return TfidfMatcher(properties)
