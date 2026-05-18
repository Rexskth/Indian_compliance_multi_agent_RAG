import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
from typing import List, Dict, Any
from backend.ingestion.vector_store import VectorStore
from backend.ingestion.embedding_pipeline import EmbeddingPipeline
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.ingestion.config import config


class RetrievalResult:
    def __init__(
        self,
        chunk_id: str,
        text: str,
        source: str,
        document_type: str,
        section_number: str,
        page_number: int,
        score: float,
        rank: int = 0
    ):
        self.chunk_id = chunk_id
        self.text = text
        self.source = source
        self.document_type = document_type
        self.section_number = section_number
        self.page_number = page_number
        self.score = score
        self.rank = rank

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source": self.source,
            "document_type": self.document_type,
            "section_number": self.section_number,
            "page_number": self.page_number,
            "score": round(self.score, 4),
            "rank": self.rank
        }


class HybridRetriever:
    def __init__(
        self,
        vector_weight: float = config.VECTOR_WEIGHT,
        bm25_weight: float = config.BM25_WEIGHT
    ):
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight

        self.vector_store = VectorStore()
        self.bm25_retriever = BM25Retriever(self.vector_store)
        self.embedding_pipeline = EmbeddingPipeline()

    def retrieve(self, query: str, top_k: int = config.TOP_K) -> List[RetrievalResult]:
        query_embedding = self.embedding_pipeline.generate_embedding(query)

        vector_results = self._vector_search(query_embedding, top_k * 2)
        bm25_results = self._bm25_search(query, top_k * 2)

        combined = self._combine_results(vector_results, bm25_results)
        reranked = self._rerank(combined, top_k)

        return reranked

    def _vector_search(self, query_embedding: np.ndarray, top_k: int) -> Dict[str, float]:
        results = self.vector_store.query(query_embedding, top_k)

        scores = {}
        if results and results["ids"]:
            for i, chunk_id in enumerate(results["ids"][0]):
                scores[chunk_id] = 1 - results["distances"][0][i]

        return scores

    def _bm25_search(self, query: str, top_k: int) -> Dict[str, float]:
        results = self.bm25_retriever.search(query, top_k)
        return {chunk_id: score for chunk_id, score in results}

    def _combine_results(
        self,
        vector_scores: Dict[str, float],
        bm25_scores: Dict[str, float]
    ) -> Dict[str, float]:
        all_ids = set(vector_scores.keys()) | set(bm25_scores.keys())

        max_vector = max(vector_scores.values()) if vector_scores else 1.0
        max_bm25 = max(bm25_scores.values()) if bm25_scores else 1.0

        combined = {}
        for chunk_id in all_ids:
            vector_norm = vector_scores.get(chunk_id, 0) / max_vector
            bm25_norm = bm25_scores.get(chunk_id, 0) / max_bm25

            combined[chunk_id] = (
                self.vector_weight * vector_norm +
                self.bm25_weight * bm25_norm
            )

        return combined

    def _rerank(self, combined_scores: Dict[str, float], top_k: int) -> List[RetrievalResult]:
        sorted_chunks = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        collection = self.vector_store.get_or_create_collection()
        ids = [chunk_id for chunk_id, _ in sorted_chunks]

        if not ids:
            return []

        retrieved = collection.get(ids=ids, include=["documents", "metadatas"])

        results = []
        for rank, (chunk_id, score) in enumerate(sorted_chunks, start=1):
            idx = retrieved["ids"].index(chunk_id)

            metadata = retrieved["metadatas"][idx]

            results.append(RetrievalResult(
                chunk_id=chunk_id,
                text=retrieved["documents"][idx],
                source=metadata.get("source", ""),
                document_type=metadata.get("document_type", ""),
                section_number=metadata.get("section_number", ""),
                page_number=metadata.get("page_number", 0),
                score=score,
                rank=rank
            ))

        return results