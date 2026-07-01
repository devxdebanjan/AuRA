"""
AuRA configuration — centralised environment loading and constants.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent          # Researchagent/
WORKSPACE_DIR = ROOT_DIR / "workspace"
CONTEXT_DIR = Path(__file__).resolve().parent / "context"  # aura/context/
DB_PATH = ROOT_DIR / "aura_state.db"

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv(ROOT_DIR / ".env")

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

# ---------------------------------------------------------------------------
# Agent defaults
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "groq:meta-llama/llama-4-scout-17b-16e-instruct"
RECURSION_LIMIT = 100

# ArXiv tool defaults
ARXIV_MAX_RESULTS = 5
ARXIV_DOC_CONTENT_CHARS_MAX = 8_000  # truncate paper text to stay lean

# Tavily tool defaults
TAVILY_MAX_RESULTS = 5


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_keys() -> list[str]:
    """Return a list of human-readable warnings for missing API keys."""
    warnings: list[str] = []
    if not GROQ_API_KEY:
        warnings.append("GROQ_API_KEY is not set — the LLM will not work.")
    if not TAVILY_API_KEY:
        warnings.append("TAVILY_API_KEY is not set — web search will fail.")
    return warnings
