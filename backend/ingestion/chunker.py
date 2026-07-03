import re
from typing import Optional
from dataclasses import dataclass
from backend.ingestion.document_parser import ExtractedPage, ParsedDocument


@dataclass
class TextChunk:
    chunk_id: str
    text: str
    source: str
    document_type: str
    document_name: str
    section_number: Optional[str]
    page_number: int
    effective_date: Optional[str] = None
    last_verified: str = "2025-01-01"
    status: str = "active"


class SemanticChunker:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_into_sentences(self, text: str) -> list[str]:
        sentence_endings = re.compile(r'(?<=[.!?])\s+')
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_token_count(self, text: str) -> int:
        words = text.split()
        return int(len(words) * 1.3)

    def chunk_page(self, page: ExtractedPage, doc_source: str) -> list[TextChunk]:
        sentences = self._split_into_sentences(page.text)
        chunks = []
        current_chunk_text = []
        current_token_count = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_tokens = self._get_token_count(sentence)

            if current_token_count + sentence_tokens > self.chunk_size and current_chunk_text:
                chunk_text = " ".join(current_chunk_text)
                chunk_id = f"{doc_source}_p{page.page_number}_c{chunk_index}"

                chunks.append(TextChunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    source=page.metadata.source,
                    document_type=page.metadata.document_type,
                    document_name=page.metadata.document_name,
                    section_number=page.metadata.section_number,
                    page_number=page.page_number,
                    effective_date=page.metadata.effective_date,
                    last_verified=page.metadata.last_verified,
                    status=page.metadata.status
                ))

                overlap_sentences = current_chunk_text[-2:] if len(current_chunk_text) >= 2 else current_chunk_text
                current_chunk_text = overlap_sentences + [sentence]
                current_token_count = sum(self._get_token_count(s) for s in current_chunk_text)
                chunk_index += 1
            else:
                current_chunk_text.append(sentence)
                current_token_count += sentence_tokens

        if current_chunk_text:
            chunk_text = " ".join(current_chunk_text)
            chunk_id = f"{doc_source}_p{page.page_number}_c{chunk_index}"

            chunks.append(TextChunk(
                chunk_id=chunk_id,
                text=chunk_text,
                source=page.metadata.source,
                document_type=page.metadata.document_type,
                document_name=page.metadata.document_name,
                section_number=page.metadata.section_number,
                page_number=page.page_number,
                effective_date=page.metadata.effective_date,
                last_verified=page.metadata.last_verified,
                status=page.metadata.status
            ))

        return chunks

    def chunk_document(self, document: ParsedDocument) -> list[TextChunk]:
        all_chunks = []
        doc_source = document.filename.replace(".pdf", "")

        for page in document.pages:
            page_chunks = self.chunk_page(page, doc_source)
            all_chunks.extend(page_chunks)

        return all_chunks

    def chunk_all_documents(self, documents: list[ParsedDocument]) -> list[TextChunk]:
        all_chunks = []
        for doc in documents:
            doc_chunks = self.chunk_document(doc)
            all_chunks.extend(doc_chunks)
            print(f"Chunked: {doc.filename} -> {len(doc_chunks)} chunks")
        return all_chunks