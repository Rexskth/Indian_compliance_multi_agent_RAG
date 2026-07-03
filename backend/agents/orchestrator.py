import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, List, Optional, Generator
from backend.agents.legal_agent import LegalAgent
from backend.agents.risk_agent import RiskAgent
from backend.agents.citation_validator import CitationValidator
from backend.retrieval.hybrid_retriever import RetrievalResult
from backend.utils.cache import two_layer_cache


class Stage:
    SEARCHING = "searching"
    ANALYZING = "analyzing"
    RISK_ASSESSMENT = "risk_assessment"
    VALIDATING = "validating"
    GENERATING = "generating"
    COMPLETE = "complete"


class QueryIntent:
    LEGAL = "legal"
    RISK = "risk"
    GENERAL = "general"
    COMPLIANCE = "compliance"


class Orchestrator:
    def __init__(self):
        self.legal_agent = LegalAgent()
        self.risk_agent = RiskAgent()
        self.citation_validator = CitationValidator()
        self.cache = two_layer_cache
        self.use_cache = True

    def classify_intent(self, query: str) -> str:
        query_lower = query.lower()

        risk_keywords = ["risk", "penalty", "fine", "punishment", "imprisonment", "jail", "offense", "violation", "non-compliance", "penal consequences"]
        compliance_keywords = ["compliance", "compliant", "requirement", "obligation", "must", "should", "need to", "mandatory"]

        if any(kw in query_lower for kw in risk_keywords):
            return QueryIntent.RISK
        elif any(kw in query_lower for kw in compliance_keywords):
            return QueryIntent.COMPLIANCE
        elif any(kw in query_lower for kw in ["explain", "what is", "define", "meaning", "understand"]):
            return QueryIntent.LEGAL
        else:
            return QueryIntent.GENERAL

    def process_query(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        if self.use_cache:
            cached_response, cache_source = self.cache.get(query)
            if cached_response:
                if cache_source == "response_cache":
                    print(f"⚡ Returning from RESPONSE CACHE (instant)")
                    cached_response['cache_hit'] = True
                    cached_response['cache_type'] = 'response'
                    return cached_response
                elif cache_source == "document_cache":
                    print(f"⚡ Returning from DOCUMENT CACHE (fast)")
                    cached_response['cache_hit'] = True
                    cached_response['cache_type'] = 'documents'
        
        intent = self.classify_intent(query)

        print(f"Intent classified: {intent}")

        legal_result = self.legal_agent.process(query)

        if intent in [QueryIntent.RISK, QueryIntent.COMPLIANCE]:
            context_results = self._get_context_results(legal_result)
            risk_result = self.risk_agent.process(query, context_results)
        else:
            risk_result = {
                "level": "low",
                "severity_score": 0.0,
                "penalties": [],
                "mitigations": [],
                "explanation": "No specific risk assessment requested"
            }

        context_results = self._get_context_results(legal_result)
        citation_result = self.citation_validator.process(
            legal_result["answer"],
            context_results
        )

        final_answer = self._construct_final_answer(
            legal_result["answer"],
            citation_result
        )

        result = {
            "answer": final_answer,
            "citations": self._format_citations(legal_result),
            "risk_level": risk_result["level"],
            "severity_score": risk_result["severity_score"],
            "risk_details": {
                "penalties": risk_result["penalties"],
                "mitigations": risk_result["mitigations"]
            },
            "confidence": citation_result["confidence"],
            "citation_validation": citation_result,
            "intent": intent,
            "sources": legal_result["sources"],
            "cache_hit": False,
            "cache_type": None
        }

        if self.use_cache:
            self.cache.cache_response(query, result)

        return result

    def process_query_streaming(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        if self.use_cache:
            cached_response, cache_source = self.cache.get(query)
            if cached_response:
                if cache_source == "response_cache":
                    print(f"⚡ Returning from RESPONSE CACHE (instant)")
                    cached_response['cache_hit'] = True
                    cached_response['cache_type'] = 'response'
                    cached_response['stage'] = Stage.COMPLETE
                    yield cached_response
                    return
                elif cache_source == "document_cache":
                    print(f"⚡ Returning from DOCUMENT CACHE (fast)")
                    cached_response['cache_hit'] = True
                    cached_response['cache_type'] = 'documents'

        yield {"stage": Stage.SEARCHING, "message": "🔍 Searching legal documents..."}

        intent = self.classify_intent(query)
        yield {"stage": Stage.ANALYZING, "message": "⚖️ Analyzing legal context..."}

        legal_result = self.legal_agent.process(query)

        yield {"stage": Stage.RISK_ASSESSMENT, "message": "📊 Assessing risk factors..."}

        if intent in [QueryIntent.RISK, QueryIntent.COMPLIANCE]:
            context_results = self._get_context_results(legal_result)
            risk_result = self.risk_agent.process(query, context_results)
        else:
            risk_result = {
                "level": "low",
                "severity_score": 0.0,
                "penalties": [],
                "mitigations": [],
                "explanation": "No specific risk assessment requested"
            }

        yield {"stage": Stage.VALIDATING, "message": "✅ Validating citations..."}

        context_results = self._get_context_results(legal_result)
        citation_result = self.citation_validator.process(
            legal_result["answer"],
            context_results
        )

        yield {"stage": Stage.GENERATING, "message": "✍️ Generating final response..."}

        final_answer = self._construct_final_answer(
            legal_result["answer"],
            citation_result
        )

        result = {
            "answer": final_answer,
            "citations": self._format_citations(legal_result),
            "risk_level": risk_result["level"],
            "severity_score": risk_result["severity_score"],
            "risk_details": {
                "penalties": risk_result["penalties"],
                "mitigations": risk_result["mitigations"]
            },
            "confidence": citation_result["confidence"],
            "citation_validation": citation_result,
            "intent": intent,
            "sources": legal_result["sources"],
            "cache_hit": False,
            "cache_type": None,
            "stage": Stage.COMPLETE
        }

        if self.use_cache:
            self.cache.cache_response(query, result)

        yield result

    def _get_context_results(self, legal_result: Dict[str, Any]) -> List[RetrievalResult]:
        from backend.retrieval.hybrid_retriever import RetrievalResult
        results = []
        for ctx in legal_result.get("context_used", []):
            results.append(RetrievalResult(
                chunk_id=ctx.get("chunk_id", ""),
                text=ctx.get("text", ""),
                source=ctx.get("source", ""),
                document_type=ctx.get("document_type", ""),
                document_name=ctx.get("document_name", ""),
                section_number=ctx.get("section_number", ""),
                page_number=ctx.get("page_number", 0),
                score=ctx.get("score", 0.0),
                rank=ctx.get("rank", 0)
            ))
        return results

    def _construct_final_answer(self, answer: str, citation_result: Dict[str, Any]) -> str:
        if not citation_result["is_valid"]:
            warning = "\n\n⚠️ NOTE: Some citations in this response may not be fully verified. Please verify with a legal expert."
            return answer + warning
        return answer

    def _format_citations(self, legal_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        citations = []
        for ctx in legal_result.get("context_used", []):
            citations.append({
                "source": ctx.get("source", "unknown"),
                "document_name": ctx.get("document_name", ""),
                "section": ctx.get("section_number", "N/A"),
                "page": ctx.get("page_number", 0),
                "text_preview": ctx.get("text", "")[:200]
            })
        return citations


orchestrator = Orchestrator()