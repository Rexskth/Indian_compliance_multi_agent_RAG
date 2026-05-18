import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rank_bm25 import BM25Okapi
import numpy as np
from backend.ingestion.vector_store import VectorStore
from backend.ingestion.chunker import TextChunk
from typing import List, Tuple


class BM25Retriever:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.bm25 = None
        self.corpus = []
        self.chunk_ids = []
        self._build_index()

    def _build_index(self):
        collection = self.vector_store.get_or_create_collection()
        results = collection.peek(limit=10000)

        self.corpus = results["documents"]
        self.chunk_ids = results["ids"]

        if self.corpus:
            tokenized_corpus = [doc.split() for doc in self.corpus]
            self.bm25 = BM25Okapi(tokenized_corpus)
            print(f"BM25 index built with {len(self.corpus)} documents")

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        if not self.bm25:
            return []

        tokenized_query = query.split()
        scores = self.bm25.get_scores(tokenized_query)

        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self.chunk_ids[idx], scores[idx]))

        return results

    def get_documents_by_ids(self, ids: List[str]) -> List[str]:
        if not self.corpus or not self.chunk_ids:
            return []

        id_to_doc = dict(zip(self.chunk_ids, self.corpus))
        return [id_to_doc.get(doc_id, "") for doc_id in ids]