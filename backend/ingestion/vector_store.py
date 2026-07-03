import chromadb
from chromadb.config import Settings
from typing import Optional
from pathlib import Path
import numpy as np
from backend.ingestion.chunker import TextChunk
from backend.ingestion.embedding_pipeline import EmbeddingPipeline
from backend.ingestion.config import config


class VectorStore:
    def __init__(self, collection_name: str = "legal_documents", persist_directory: Optional[Path] = None):
        self.collection_name = collection_name
        self.persist_directory = persist_directory or config.CHROMA_DB_PATH
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(str(self.persist_directory))
        self.collection = None
        self.embedding_pipeline = EmbeddingPipeline()

    def create_collection(self):
        dimension = self.embedding_pipeline.get_embedding_dimension()
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
            get_or_create=True
        )
        print(f"Collection '{self.collection_name}' created with dimension {dimension}")

    def get_or_create_collection(self):
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"Collection '{self.collection_name}' loaded")
        except Exception:
            self.create_collection()
        return self.collection

    def add_chunks(self, chunks: list[TextChunk], embeddings: list[np.ndarray]):
        if not self.collection:
            self.get_or_create_collection()

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "source": chunk.source,
                "document_type": chunk.document_type,
                "document_name": chunk.document_name,
                "section_number": chunk.section_number or "",
                "page_number": chunk.page_number,
                "effective_date": chunk.effective_date or "",
                "last_verified": chunk.last_verified,
                "status": chunk.status
            }
            for chunk in chunks
        ]

        embeddings_list = [emb.tolist() for emb in embeddings]

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings_list
        )

        print(f"Added {len(chunks)} chunks to collection")

    def query(self, query_embedding: np.ndarray, top_k: int = 5) -> dict:
        if not self.collection:
            self.get_or_create_collection()

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )

        return results

    def delete_collection(self):
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"Collection '{self.collection_name}' deleted")
        except Exception as e:
            print(f"Error deleting collection: {e}")