import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import re
from typing import List, Dict, Any, Tuple
from backend.retrieval.hybrid_retriever import RetrievalResult
from backend.llm.llm_client import llm_client


class CitationValidation:
    def __init__(
        self,
        is_valid: bool,
        confidence: float,
        validated_citations: List[Dict[str, Any]],
        issues: List[str]
    ):
        self.is_valid = is_valid
        self.confidence = confidence
        self.validated_citations = validated_citations
        self.issues = issues

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "confidence": round(self.confidence, 2),
            "validated_citations": self.validated_citations,
            "issues": self.issues
        }


class CitationValidator:
    def __init__(self):
        self.system_prompt = """You are a citation validation expert.
Your task is to verify that legal citations in responses are actually present in the source context.
Flag any citations that appear to be fabricated or not supported by the context."""

    def extract_citations(self, text: str) -> List[str]:
        patterns = [
            r"Section\s+\d+[A-Z]?",
            r"Section\s+\d+[A-Z]?\s+\w+",
            r"Rule\s+\d+",
            r"Chapter\s+[IVXLCDM]+",
            r"Article\s+\d+",
            r"s\.\s*\d+",
            r"Rule\s+\d+[A-Z]?"
        ]

        citations = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            citations.extend(matches)

        return list(set(citations))

    def validate_citations(
        self,
        answer: str,
        context_results: List[RetrievalResult]
    ) -> CitationValidation:
        extracted_citations = self.extract_citations(answer)

        if not extracted_citations:
            return CitationValidation(
                is_valid=True,
                confidence=1.0,
                validated_citations=[],
                issues=["No explicit citations found in answer"]
            )

        context_text = " ".join([r.text for r in context_results])

        prompt = f"""Validate whether the following citations are present in the legal context.
For each citation, determine if it exists in the context or appears to be fabricated.

Context:
{context_text[:2000]}

Citations to validate:
{', '.join(extracted_citations)}

Respond in this exact format:
VALID: [yes/no] - list of valid citations
INVALID: [yes/no] - list of invalid/fabricated citations
CONFIDENCE: [0-1] - confidence score
ISSUES: [any concerns about the citations]"""

        response = llm_client.generate(prompt, self.system_prompt)

        return self._parse_validation_response(response, extracted_citations)

    def _parse_validation_response(
        self,
        response: str,
        extracted_citations: List[str]
    ) -> CitationValidation:
        is_valid = True
        confidence = 0.9
        issues = []

        valid_citations = []
        invalid_citations = []

        for line in response.split("\n"):
            if line.startswith("VALID:"):
                valid_text = line.split(":")[1].strip()
                if valid_text and valid_text.lower() != "none":
                    valid_citations = [v.strip() for v in valid_text.split(",")]
            elif line.startswith("INVALID:"):
                invalid_text = line.split(":")[1].strip()
                if invalid_text and invalid_text.lower() != "none":
                    invalid_citations = [i.strip() for i in invalid_text.split(",")]
                    is_valid = False
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("ISSUES:"):
                issues_text = line.split(":")[1].strip()
                if issues_text and issues_text.lower() != "none":
                    issues = [i.strip() for i in issues_text.split(",")]

        validated_citations = [
            {"citation": c, "valid": True} for c in valid_citations
        ] + [
            {"citation": c, "valid": False} for c in invalid_citations
        ]

        return CitationValidation(
            is_valid=is_valid,
            confidence=confidence,
            validated_citations=validated_citations,
            issues=issues
        )

    def process(self, answer: str, context_results: List[RetrievalResult]) -> Dict[str, Any]:
        validation = self.validate_citations(answer, context_results)
        return validation.to_dict()