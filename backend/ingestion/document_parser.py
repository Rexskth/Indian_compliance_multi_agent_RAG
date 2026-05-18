import pdfplumber
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import re


@dataclass
class DocumentMetadata:
    source: str
    document_type: str
    section_number: Optional[str] = None
    effective_date: Optional[str] = None
    last_verified: str = "2025-01-01"
    status: str = "active"
    page_number: int = 0


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    metadata: DocumentMetadata


@dataclass
class ParsedDocument:
    filename: str
    pages: list[ExtractedPage] = field(default_factory=list)


class DocumentParser:
    DOCUMENT_TYPE_MAP = {
        "dpdpa_2023": "act",
        "it_act_2000": "act",
        "companies_act_2013": "act"
    }

    @staticmethod
    def extract_section_number(text: str) -> Optional[str]:
        patterns = [
            r"Section\s+(\d+[A-Z]?)",
            r"Rule\s+(\d+[A-Z]?)",
            r"Chapter\s+([IVXLCDM]+)",
            r"Article\s+(\d+)",
            r"Regulation\s+(\d+)"
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def parse_pdf(self, pdf_path: Path) -> ParsedDocument:
        filename = pdf_path.name
        doc_key = filename.replace(".pdf", "").replace("The_", "").replace("_", " ").strip()

        doc_type_map = {
            "DPDPA_act_2023": "dpdpa_2023",
            "The_Information_Technology_Act_2000": "it_act_2000",
            "Companies_Act_2013": "companies_act_2013"
        }
        doc_id = doc_type_map.get(filename, "unknown")

        parsed_doc = ParsedDocument(filename=filename)

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text or not text.strip():
                    continue

                section_number = self.extract_section_number(text)

                metadata = DocumentMetadata(
                    source=doc_id,
                    document_type=self.DOCUMENT_TYPE_MAP.get(doc_id, "act"),
                    section_number=section_number,
                    page_number=page_num
                )

                parsed_doc.pages.append(ExtractedPage(
                    page_number=page_num,
                    text=text,
                    metadata=metadata
                ))

        return parsed_doc

    def parse_all_pdfs(self, pdf_files: list[Path]) -> list[ParsedDocument]:
        all_documents = []
        for pdf_path in pdf_files:
            try:
                parsed = self.parse_pdf(pdf_path)
                all_documents.append(parsed)
                print(f"Parsed: {pdf_path.name} -> {len(parsed.pages)} pages")
            except Exception as e:
                print(f"Error parsing {pdf_path.name}: {e}")
        return all_documents