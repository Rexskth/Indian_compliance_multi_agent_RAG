import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List
from backend.ingestion.vector_store import VectorStore
from backend.ingestion.config import config


class ResponseCache:
    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)

    def _normalize_query(self, query: str) -> str:
        return query.lower().strip()

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        normalized = self._normalize_query(query)
        
        if normalized in self.cache:
            entry = self.cache[normalized]
            
            if datetime.now() - entry['timestamp'] < self.ttl:
                return entry['data']
            else:
                del self.cache[normalized]
        
        return None

    def set(self, query: str, data: Dict[str, Any]) -> None:
        normalized = self._normalize_query(query)
        
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        self.cache[normalized] = {
            'data': data,
            'timestamp': datetime.now()
        }

    def _evict_oldest(self) -> None:
        if not self.cache:
            return
        
        oldest_key = min(self.cache, key=lambda k: self.cache[k]['timestamp'])
        del self.cache[oldest_key]

    def clear(self) -> None:
        self.cache.clear()

    def size(self) -> int:
        return len(self.cache)


class TwoLayerCache:
    def __init__(
        self,
        response_cache_size: int = 1000,
        response_ttl_hours: int = 24
    ):
        self.response_cache = ResponseCache(
            max_size=response_cache_size,
            ttl_hours=response_ttl_hours
        )
        self.vector_store = None

    def _get_vector_store(self):
        if self.vector_store is None:
            self.vector_store = VectorStore()
        return self.vector_store

    def get_cached_response(self, query: str) -> Optional[Dict[str, Any]]:
        return self.response_cache.get(query)

    def cache_response(self, query: str, response_data: Dict[str, Any]) -> None:
        self.response_cache.set(query, response_data)

    def get_cached_documents(self, query: str, top_k: int = None) -> Tuple[List, bool]:
        top_k = top_k or config.TOP_K
        vector_store = self._get_vector_store()
        
        from backend.ingestion.embedding_pipeline import EmbeddingPipeline
        embedding_pipeline = EmbeddingPipeline()
        query_embedding = embedding_pipeline.generate_embedding(query)
        
        results = vector_store.query(query_embedding, top_k)
        
        if results and results.get('ids') and len(results['ids'][0]) > 0:
            return results, True
        
        return [], False

    def get(self, query: str) -> Tuple[Optional[Dict[str, Any]], str]:
        cached_response = self.get_cached_response(query)
        
        if cached_response:
            return cached_response, "response_cache"
        
        cached_docs, found = self.get_cached_documents(query)
        
        if found:
            return {"cached_documents": cached_docs}, "document_cache"
        
        return None, "none"

    def clear_all(self) -> None:
        self.response_cache.clear()


two_layer_cache = TwoLayerCache()