import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    CHROMA_DB_PATH: Path = PROJECT_ROOT / "chroma_db"
    PDFs_PATH: Path = PROJECT_ROOT

    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 100

    TOP_K: int = 7
    VECTOR_WEIGHT: float = 0.7
    BM25_WEIGHT: float = 0.3

    EMBED_MODEL: str = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
    LLM_MODEL: str = "baidu/cobuddy:free"

    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")

    @classmethod
    def get_pdf_files(cls) -> list[Path]:
        pdf_files = list(cls.PDFs_PATH.glob("*.pdf"))
        pdf_mapping = {
            "DPDPA_act_2023.pdf": "dpdpa_2023",
            "The_Information_Technology_Act_2000.pdf": "it_act_2000",
            "Companies_Act_2013.pdf": "companies_act_2013"
        }
        return pdf_files


config = Config()