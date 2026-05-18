import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import List, Dict, Any
from backend.retrieval.hybrid_retriever import RetrievalResult
from backend.llm.llm_client import llm_client


class RiskAssessment:
    def __init__(
        self,
        level: str,
        severity_score: float,
        penalties: List[str],
        mitigations: List[str],
        explanation: str
    ):
        self.level = level
        self.severity_score = severity_score
        self.penalties = penalties
        self.mitigations = mitigations
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "severity_score": round(self.severity_score, 2),
            "penalties": self.penalties,
            "mitigations": self.mitigations,
            "explanation": self.explanation
        }


class RiskAgent:
    def __init__(self):
        self.system_prompt = """You are a legal risk assessment expert specializing in Indian compliance laws.
Your task is to assess the legal risk level, potential penalties, and suggest mitigations based on the legal context.
Always be accurate about penalty provisions - do not fabricate amounts or consequences."""

    def assess_risk(
        self,
        query: str,
        context_results: List[RetrievalResult]
    ) -> RiskAssessment:
        context_text = self._build_risk_context(context_results)

        prompt = f"""Analyze the legal risk associated with the following query and context.
Determine:
1. Risk level (low/medium/high/critical)
2. Severity score (0-10)
3. Potential penalties (if any)
4. Mitigation suggestions

User Query: {query}

Legal Context:
{context_text}

Respond in this exact format:
RISK_LEVEL: [low/medium/high/critical]
SEVERITY: [0-10]
PENALTIES: [list any penalties mentioned]
MITIGATIONS: [list mitigation steps]
EXPLANATION: [brief explanation]"""

        response = llm_client.generate(prompt, self.system_prompt)

        return self._parse_risk_response(response)

    def _build_risk_context(self, results: List[RetrievalResult]) -> str:
        context_parts = []
        for r in results[:5]:
            context_parts.append(
                f"[{r.source.upper()}, Section {r.section_number or 'N/A'}]\n{r.text[:500]}\n"
            )
        return "\n".join(context_parts)

    def _parse_risk_response(self, response: str) -> RiskAssessment:
        lines = response.split("\n")

        level = "medium"
        severity = 5.0
        penalties = []
        mitigations = []
        explanation = response

        for line in lines:
            if line.startswith("RISK_LEVEL:"):
                level = line.split(":")[1].strip().lower()
            elif line.startswith("SEVERITY:"):
                try:
                    severity = float(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("PENALTIES:"):
                penalties_text = line.split(":")[1].strip()
                if penalties_text and penalties_text.lower() != "none":
                    penalties = [p.strip() for p in penalties_text.split(",")]
            elif line.startswith("MITIGATIONS:"):
                mitigations_text = line.split(":")[1].strip()
                if mitigations_text and mitigations_text.lower() != "none":
                    mitigations = [m.strip() for m in mitigations_text.split(",")]

        return RiskAssessment(
            level=level,
            severity_score=severity,
            penalties=penalties,
            mitigations=mitigations,
            explanation=explanation
        )

    def process(self, query: str, context_results: List[RetrievalResult]) -> Dict[str, Any]:
        assessment = self.assess_risk(query, context_results)
        return assessment.to_dict()