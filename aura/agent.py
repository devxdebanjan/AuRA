"""
AuRA agent factory — creates the fully-wired orchestrator agent.

This is the heart of the system.  It assembles:
- Groq LLM via deepagents model string
- FilesystemBackend for VFS context offloading
- SqliteSaver for SQL checkpointing
- Three specialised subagents
- Hybrid search tools
- AGENTS.md context engineering
"""

import shutil
import sqlite3
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.sqlite import SqliteSaver

from aura.config import (
    CONTEXT_DIR,
    DB_PATH,
    DEFAULT_MODEL,
    RECURSION_LIMIT,
    WORKSPACE_DIR,
)
from aura.subagents import ALL_SUBAGENTS
from aura.tools import ALL_TOOLS

# ---------------------------------------------------------------------------
# Orchestrator system prompt
# ---------------------------------------------------------------------------
ORCHESTRATOR_PROMPT = """\
You are AuRA (Autonomous Research Agent) — an advanced multi-agent research
system.  Your job is to autonomously plan, execute, and synthesise complex
technical research.

DELEGATION RULE:
Whenever you need to delegate work to a subagent, you MUST call the `task` tool.
Do NOT attempt to call the subagent name (like 'academic-synthesizer') directly.
The `task` tool takes two parameters:
- `subagent_type`: The name of the subagent (must be one of: 'academic-synthesizer', 'web-scraper', or 'report-synthesizer').
- `description`: The detailed instructions for that subagent.

WORKFLOW:
1. PLAN: Always start by calling write_todos to decompose the user's query
   into discrete research tasks.  Update statuses as you progress.

2. ACADEMIC RESEARCH: Call the `task` tool with `subagent_type="academic-synthesizer"` to search ArXiv for peer-reviewed papers. Give it a focused query.

3. WEB RESEARCH: Call the `task` tool with `subagent_type="web-scraper"` to search the web for current implementations and news. Give it a focused query.

4. OFFLOAD: If you receive large raw data, write it to the virtual
   filesystem (workspace/raw/) immediately.  Keep your context lean.

5. CROSS-REFERENCE: After gathering data, compare academic findings with
   web findings.  Note agreements, contradictions, and gaps.

6. SYNTHESISE: Call the `task` tool with `subagent_type="report-synthesizer"` to produce the final Markdown research report from the VFS notes.

7. DELIVER: Present the final report to the user with an executive summary,
   confidence score, and full source citations.

RULES:
- You MUST use native tool calling. Do NOT generate XML tags like `<function=...>` or markdown JSON blocks to call tools.
- Never call tools with subagent names directly. Always call the `task` tool with the correct `subagent_type` parameter.
- Never fabricate citations, paper titles, or URLs.
- Always cite sources in your final output.
- Use the hybrid_search tool for quick dual-source queries.
- Use individual arxiv_search / web_search tools for targeted lookups.
- Offload bulky content to files; keep conversation concise.
"""


def _seed_context_files(workspace: Path) -> list[str]:
    """Copy AGENTS.md into the workspace and return VFS memory paths.

    The FilesystemBackend maps VFS paths to real files under its root_dir.
    We copy our context file into the workspace so the agent can read it.
    """
    memory_paths: list[str] = []
    src = CONTEXT_DIR / "AGENTS.md"
    if src.exists():
        dst = workspace / "AGENTS.md"
        shutil.copy2(src, dst)
        # VFS path is relative to the backend root_dir, prefixed with /
        memory_paths.append("/AGENTS.md")
    return memory_paths


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------
def create_aura_agent(
    model: str = DEFAULT_MODEL,
    workspace_dir: str | Path | None = None,
    db_path: str | Path | None = None,
    checkpointer=None,
):
    """Create and return a fully-configured AuRA orchestrator agent.

    Parameters
    ----------
    model : str
        Model string in ``provider:model`` format (default: Groq qwen3-32b).
    workspace_dir : str | Path | None
        Root directory for the virtual filesystem.  Defaults to
        ``Researchagent/workspace/``.
    db_path : str | Path | None
        Path for the SQLite checkpoint database.  Defaults to
        ``Researchagent/aura_state.db``.
    checkpointer : optional
        Pre-configured LangGraph checkpointer.  If not provided, a
        ``SqliteSaver`` is created at *db_path*.

    Returns
    -------
    agent
        A compiled LangGraph agent (the return value of
        ``create_deep_agent``).
    checkpointer
        The checkpointer instance (useful if the caller needs to manage
        the connection lifecycle).
    """
    workspace = Path(workspace_dir) if workspace_dir else WORKSPACE_DIR
    workspace.mkdir(parents=True, exist_ok=True)

    # Ensure subdirectories exist
    for subdir in ("raw", "notes", "reports"):
        (workspace / subdir).mkdir(exist_ok=True)

    # --- SQL Checkpointer ---------------------------------------------------
    if checkpointer is None:
        db = str(db_path) if db_path else str(DB_PATH)
        conn = sqlite3.connect(db, check_same_thread=False)
        checkpointer = SqliteSaver(conn)
        checkpointer.setup()

    # --- Filesystem backend (VFS) -------------------------------------------
    backend = FilesystemBackend(root_dir=str(workspace), virtual_mode=True)

    # --- Seed context files into workspace ----------------------------------
    memory_paths = _seed_context_files(workspace)

    # --- Assemble -----------------------------------------------------------
    agent = create_deep_agent(
        model=model,
        tools=ALL_TOOLS,
        system_prompt=ORCHESTRATOR_PROMPT,
        subagents=ALL_SUBAGENTS,
        backend=backend,
        checkpointer=checkpointer,
        memory=None,
    )

    return agent, checkpointer
