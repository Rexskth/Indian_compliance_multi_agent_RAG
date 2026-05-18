import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.ingestion.config import config
from backend.ingestion.document_parser import DocumentParser
from backend.ingestion.chunker import SemanticChunker
from backend.ingestion.embedding_pipeline import EmbeddingPipeline
from backend.ingestion.vector_store import VectorStore


def main():
    print("=" * 60)
    print("PHASE 1: DATA INGESTION PIPELINE")
    print("=" * 60)

    print("\n[1/5] Getting PDF files...")
    pdf_files = config.get_pdf_files()
    print(f"Found {len(pdf_files)} PDFs: {[f.name for f in pdf_files]}")

    print("\n[2/5] Parsing PDFs...")
    parser = DocumentParser()
    documents = parser.parse_all_pdfs(pdf_files)
    total_pages = sum(len(doc.pages) for doc in documents)
    print(f"Total pages extracted: {total_pages}")

    print("\n[3/5] Creating semantic chunks...")
    chunker = SemanticChunker(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP
    )
    chunks = chunker.chunk_all_documents(documents)
    print(f"Total chunks created: {len(chunks)}")

    print("\n[4/5] Generating embeddings...")
    embedding_pipeline = EmbeddingPipeline()
    embeddings = embedding_pipeline.generate_embeddings_batch(chunks)
    print(f"Generated {len(embeddings)} embeddings")

    print("\n[5/5] Storing in ChromaDB...")
    vector_store = VectorStore()
    vector_store.add_chunks(chunks, embeddings)

    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"Documents processed: {len(documents)}")
    print(f"Pages extracted: {total_pages}")
    print(f"Chunks created: {len(chunks)}")
    print(f"ChromaDB collection: {vector_store.collection_name}")


if __name__ == "__main__":
    main()