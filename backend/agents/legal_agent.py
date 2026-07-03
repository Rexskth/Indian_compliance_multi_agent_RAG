import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import List, Dict, Any
from backend.retrieval.hybrid_retriever import HybridRetriever, RetrievalResult
from backend.llm.llm_client import llm_client


class LegalAgent:
    def __init__(self):
        self.retriever = HybridRetriever()
        self.system_prompt = """You are a legal expert specializing in Indian laws (DPDPA 2023, IT Act 2000, Companies Act 2013).
Your task is to provide accurate, citation-grounded legal information based on the provided context.
Always cite the source section and document when making legal claims.
If you are unsure about something, explicitly state that the information may require verification from a legal expert.
Do not fabricate section numbers, penalties, or legal text."""

    def retrieve_context(self, query: str, top_k: int = 7) -> List[RetrievalResult]:
        return self.retriever.retrieve(query, top_k)

    def synthesize_answer(
        self,
        query: str,
        context_results: List[RetrievalResult]
    ) -> Dict[str, Any]:
        context_text = self._build_context(context_results)

        prompt = f"""Based on the following legal context, answer the user's question.
If the context doesn't contain sufficient information to answer the question, say so explicitly.

User Question: {query}

Legal Context:
{context_text}

Provide a clear, accurate answer with proper citations. Format citations as [Source: Document, Section, Page]."""

        answer = llm_client.generate(prompt, self.system_prompt)

        if "fallback response" in answer.lower():
            answer = self._build_fallback_answer(query, context_text)

        return {
            "answer": answer,
            "context_used": [r.to_dict() for r in context_results],
            "sources": list(set([r.document_name or r.source for r in context_results if r.document_name or r.source]))
        }

    def _build_fallback_answer(self, query: str, context_text: str) -> str:
        return f"""Based on the retrieved legal documents, here is relevant information for your query:

**Query:** {query}

**Relevant Legal Context:**

{context_text[:2000]}

---

**Note:** This response is generated from the RAG retrieval system. To enable AI-powered synthesis, please configure the OPENROUTER_API_KEY in your .env file.

The system retrieved {7} relevant legal sections that may contain information related to your query. Please review the citations above for the specific sources."""

    def _build_context(self, results: List[RetrievalResult]) -> str:
        context_parts = []
        for r in results:
            doc_name = r.document_name or r.source.upper()
            section_info = f"Section: {r.section_number}" if r.section_number else "Section: N/A"
            context_parts.append(
                f"[{doc_name}, {section_info}, Page {r.page_number}]\n{r.text}\n"
            )
        return "\n".join(context_parts)

    def process(self, query: str) -> Dict[str, Any]:
        context_results = self.retrieve_context(query)
        return self.synthesize_answer(query, context_results)