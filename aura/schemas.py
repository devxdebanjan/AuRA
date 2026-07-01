"""
AuRA Pydantic schemas — structured output models for subagent responses.
"""

from pydantic import BaseModel, Field


class AcademicFinding(BaseModel):
    """A single finding sourced from ArXiv academic literature."""

    title: str = Field(description="Paper title")
    authors: list[str] = Field(description="List of author names")
    abstract_summary: str = Field(
        description="Concise summary of the paper's abstract (2-3 sentences)"
    )
    arxiv_url: str = Field(description="URL to the ArXiv paper page")
    relevance_score: float = Field(
        ge=0.0, le=1.0,
        description="How relevant this paper is to the research query (0-1)",
    )


class WebFinding(BaseModel):
    """A single finding sourced from web search."""

    title: str = Field(description="Page or article title")
    url: str = Field(description="Source URL")
    snippet: str = Field(description="Key excerpt or summary from the source")
    source_type: str = Field(
        description="Type of source: blog, docs, news, repo, tutorial, etc."
    )


class ResearchReport(BaseModel):
    """The final aggregated research report produced by the synthesiser."""

    topic: str = Field(description="The research topic / original query")
    executive_summary: str = Field(
        description="High-level summary of findings (1-2 paragraphs)"
    )
    academic_findings: list[AcademicFinding] = Field(
        default_factory=list,
        description="Findings from peer-reviewed / ArXiv literature",
    )
    web_findings: list[WebFinding] = Field(
        default_factory=list,
        description="Findings from web search (blogs, docs, news)",
    )
    synthesis: str = Field(
        description=(
            "Deep synthesis cross-referencing academic and web findings. "
            "Highlight agreements, contradictions, and knowledge gaps."
        )
    )
    methodology_notes: str = Field(
        description="Brief description of the search methodology used"
    )
    sources_cited: list[str] = Field(
        default_factory=list,
        description="Flat list of all URLs / DOIs cited in this report",
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Overall confidence in the report's accuracy (0-1)",
    )
