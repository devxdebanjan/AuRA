"""
AuRA custom tools — ArXiv academic search, Tavily web search, and hybrid.

Uses the ``arxiv`` library directly (v4.0.0+) instead of the deprecated
langchain-community ArxivAPIWrapper, which is incompatible with arxiv>=4.
"""

from typing import Literal

import arxiv
from tavily import TavilyClient

from aura.config import (
    ARXIV_DOC_CONTENT_CHARS_MAX,
    ARXIV_MAX_RESULTS,
    TAVILY_API_KEY,
    TAVILY_MAX_RESULTS,
)

# ---------------------------------------------------------------------------
# Clients (initialised lazily on first call so import never fails)
# ---------------------------------------------------------------------------
_arxiv_client: arxiv.Client | None = None
_tavily_client: TavilyClient | None = None


def _get_arxiv_client() -> arxiv.Client:
    global _arxiv_client
    if _arxiv_client is None:
        _arxiv_client = arxiv.Client()
    return _arxiv_client


def _get_tavily_client() -> TavilyClient:
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    return _tavily_client


# ---------------------------------------------------------------------------
# ArXiv search
# ---------------------------------------------------------------------------
def arxiv_search(query: str, max_results: int = ARXIV_MAX_RESULTS) -> str:
    """Search ArXiv for peer-reviewed academic papers and pre-prints.

    Returns structured text with title, authors, abstract excerpt, and URL
    for each matching paper.  Use this tool when you need rigorous,
    scientific literature to establish factual baselines.

    Args:
        query: The academic search query (e.g. "transformer attention efficiency").
        max_results: Maximum number of papers to return (default 5).
    """
    client = _get_arxiv_client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    sections: list[str] = []
    try:
        for i, result in enumerate(client.results(search), 1):
            authors = ", ".join(a.name for a in result.authors[:5])
            if len(result.authors) > 5:
                authors += f" (+{len(result.authors) - 5} more)"

            abstract = result.summary.replace("\n", " ").strip()
            if len(abstract) > ARXIV_DOC_CONTENT_CHARS_MAX:
                abstract = abstract[:ARXIV_DOC_CONTENT_CHARS_MAX] + "..."

            published = result.published.strftime("%Y-%m-%d") if result.published else "N/A"

            sections.append(
                f"[{i}] {result.title}\n"
                f"    Authors: {authors}\n"
                f"    Published: {published}\n"
                f"    URL: {result.entry_id}\n"
                f"    Abstract: {abstract}"
            )
    except Exception as exc:
        return f"ArXiv search failed: {exc}"

    if not sections:
        return "No ArXiv results found."
    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Tavily web search
# ---------------------------------------------------------------------------
def web_search(
    query: str,
    max_results: int = TAVILY_MAX_RESULTS,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> dict:
    """Run a real-time web search via the Tavily API.

    Use this tool to find modern implementations, industry documentation,
    blog posts, tutorials, and recent news.  Pair with arxiv_search for
    cross-verified, high-fidelity research.

    Args:
        query: The web search query.
        max_results: Maximum results to return (default 5).
        topic: Filter by topic — "general", "news", or "finance".
        include_raw_content: If True, includes the full raw page content
            (warning: can be very large — prefer writing to VFS).
    """
    client = _get_tavily_client()
    try:
        results = client.search(
            query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic,
        )
    except Exception as exc:
        return {"error": f"Tavily search failed: {exc}"}
    return results


# ---------------------------------------------------------------------------
# Hybrid search (ArXiv + Tavily combined)
# ---------------------------------------------------------------------------
def hybrid_search(query: str, max_results: int = 3) -> str:
    """Run a combined academic + web search and return a unified result set.

    This tool queries BOTH ArXiv (peer-reviewed papers) and Tavily (web)
    simultaneously and labels each result's provenance so you can
    cross-reference scientific baselines against current implementations.

    Args:
        query: The research query.
        max_results: Maximum results PER source (default 3 each).
    """
    sections: list[str] = []

    # --- Academic results ---
    sections.append("=== ACADEMIC SOURCES (ArXiv) ===")
    academic = arxiv_search(query, max_results=max_results)
    sections.append(academic if academic else "(no ArXiv results)")

    # --- Web results ---
    sections.append("\n=== WEB SOURCES (Tavily) ===")
    web = web_search(query, max_results=max_results)
    if isinstance(web, dict) and "results" in web:
        for i, r in enumerate(web["results"], 1):
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            snippet = r.get("content", "")[:500]
            sections.append(f"\n[{i}] {title}\n    URL: {url}\n    {snippet}")
    elif isinstance(web, dict) and "error" in web:
        sections.append(web["error"])
    else:
        sections.append("(no web results)")

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Convenience: list of all tool callables for the orchestrator
# ---------------------------------------------------------------------------
ALL_TOOLS = [arxiv_search, web_search, hybrid_search]
