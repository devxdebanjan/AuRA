"""
AuRA subagent definitions — specialised child agents for research tasks.

Each subagent runs in an isolated context window and communicates with the
orchestrator only through its final answer.  Defined as dicts suitable for
passing to ``create_deep_agent(subagents=[...])``.
"""

from aura.schemas import ResearchReport
from aura.tools import arxiv_search, web_search

# ---------------------------------------------------------------------------
# 1. Academic Synthesizer — ArXiv deep-dives
# ---------------------------------------------------------------------------
ACADEMIC_SYNTHESIZER = {
    "name": "academic-synthesizer",
    "description": (
        "Searches ArXiv for peer-reviewed academic papers and pre-prints "
        "on a given topic.  Returns structured summaries of the most "
        "relevant papers with titles, authors, abstracts, and URLs.  "
        "Use this for establishing factual, scientific baselines."
    ),
    "system_prompt": (
        "You are the Academic Synthesizer — a research subagent specialised "
        "in scientific literature.\n\n"
        "INSTRUCTIONS:\n"
        "1. Use the arxiv_search tool to find relevant papers.\n"
        "2. For each paper, extract: title, authors, a 2-3 sentence "
        "abstract summary, and the ArXiv URL.\n"
        "3. Assess each paper's relevance to the query on a 0-1 scale.\n"
        "4. If a paper's full text is very long, write the raw content to "
        "the virtual filesystem under /workspace/raw/ and reference the "
        "file path in your summary.\n"
        "5. Return your findings as a structured list.\n"
        "6. Never fabricate paper titles, authors, or URLs."
    ),
    "tools": [arxiv_search],
}

# ---------------------------------------------------------------------------
# 2. Web Scraper — Tavily real-time web search
# ---------------------------------------------------------------------------
WEB_SCRAPER = {
    "name": "web-scraper",
    "description": (
        "Searches the web via Tavily for modern implementations, industry "
        "documentation, blog posts, tutorials, and recent news on a given "
        "topic.  Use this for finding current, practical information that "
        "complements academic literature."
    ),
    "system_prompt": (
        "You are the Web Scraper — a research subagent specialised in "
        "real-time web intelligence.\n\n"
        "INSTRUCTIONS:\n"
        "1. Use the web_search tool to find relevant web content.\n"
        "2. For each result, extract: title, URL, a concise snippet, and "
        "classify the source type (blog, docs, news, repo, tutorial).\n"
        "3. If raw page content is very large, write it to the virtual "
        "filesystem under /workspace/raw/ and reference the file path.\n"
        "4. Prefer authoritative sources (official docs, reputable blogs, "
        "major publications) over low-quality content.\n"
        "5. Return your findings as a structured list.\n"
        "6. Never fabricate URLs or source content."
    ),
    "tools": [web_search],
}

# ---------------------------------------------------------------------------
# 3. Report Synthesizer — final aggregation and report generation
# ---------------------------------------------------------------------------
REPORT_SYNTHESIZER = {
    "name": "report-synthesizer",
    "description": (
        "Reads research notes from the virtual filesystem and produces a "
        "final, comprehensive research report.  Use this AFTER the "
        "academic-synthesizer and web-scraper have completed their work.  "
        "It cross-references academic and web findings, identifies "
        "agreements and contradictions, and produces a Markdown report."
    ),
    "system_prompt": (
        "You are the Report Synthesizer — a research subagent specialised "
        "in producing polished, comprehensive research reports.\n\n"
        "INSTRUCTIONS:\n"
        "1. Read ALL files in /workspace/notes/ and /workspace/raw/ using "
        "the file system tools (ls, read_file).\n"
        "2. Cross-reference academic findings with web findings.\n"
        "3. Identify: agreements (both sources confirm), contradictions "
        "(sources disagree), and gaps (only one source covers).\n"
        "4. Produce a Markdown research report with these sections:\n"
        "   - Executive Summary\n"
        "   - Academic Literature Review\n"
        "   - Current Industry Landscape\n"
        "   - Cross-Reference Analysis\n"
        "   - Conclusions & Confidence Assessment\n"
        "   - Sources Cited\n"
        "5. Write the final report to /workspace/reports/ as a .md file.\n"
        "6. Return a brief summary of the report along with the file path.\n"
        "7. Assign a confidence score (0-1) based on source quality and "
        "agreement between academic and web findings."
    ),
    "tools": [],  # relies on built-in VFS tools (read_file, ls, etc.)
    "response_format": ResearchReport,
}

# ---------------------------------------------------------------------------
# Convenience: list of all subagent configs
# ---------------------------------------------------------------------------
ALL_SUBAGENTS = [ACADEMIC_SYNTHESIZER, WEB_SCRAPER, REPORT_SYNTHESIZER]
