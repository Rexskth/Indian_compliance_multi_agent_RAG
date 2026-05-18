from sentence_transformers import SentenceTransformer
from typing import Optional
from backend.ingestion.config import config
from backend.ingestion.chunker import TextChunk
import numpy as np


class EmbeddingPipeline:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or config.EMBED_MODEL
        self.model = None
        self._load_model()

    def _load_model(self):
        print(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("Embedding model loaded")

    def generate_embedding(self, text: str) -> np.ndarray:
        embedding = self.model.encode(text, show_progress_bar=False)
        return embedding

    def generate_embeddings_batch(self, chunks: list[TextChunk]) -> list[np.ndarray]:
        texts = [chunk.text for chunk in chunks]
        embeddings = self.model.encode(texts, show_progress_bar=True, batch_size=32)
        return embeddings

    def get_embedding_dimension(self) -> int:
        test_embedding = self.generate_embedding("test")
        return len(test_embedding)