"""
AuRA Streamlit UI — research-focused interface for the Autonomous Research Agent.

Run with:  streamlit run app.py
"""

import os
import uuid

import streamlit as st
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv()

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

from aura.config import DEFAULT_MODEL, WORKSPACE_DIR, validate_keys
from aura.subagents import ALL_SUBAGENTS
from aura.tools import ALL_TOOLS

# ---------------------------------------------------------------------------
# Orchestrator system prompt (same as agent.py)
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


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------
def extract_text(content) -> str:
    """AIMessage.content may be a plain string or a list of content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(content)


def render_steps(messages):
    """Show the agent's intermediate work: tool calls, todos, subagent tasks."""
    for msg in messages:
        msg_type = getattr(msg, "type", "")
        if msg_type == "ai" and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                name, args = tc["name"], tc["args"]
                if name == "write_todos":
                    with st.expander("Planning — write_todos", expanded=False):
                        for todo in args.get("todos", []):
                            status = todo.get("status", "pending")
                            icon = {
                                "pending": "[ ]",
                                "in_progress": "[~]",
                                "completed": "[x]",
                            }.get(status, "[ ]")
                            st.markdown(
                                f"`{icon}` {todo.get('content', todo)}"
                            )
                elif name == "task":
                    subagent_name = args.get("subagent_type", "task")
                    with st.expander(
                        f"Subagent — {subagent_name}", expanded=False
                    ):
                        st.markdown(args.get("description", ""))
                elif name == "arxiv_search":
                    with st.expander(
                        f'ArXiv search — "{args.get("query", "")}"',
                        expanded=False,
                    ):
                        st.json(args)
                elif name == "web_search":
                    with st.expander(
                        f'Web search — "{args.get("query", "")}"',
                        expanded=False,
                    ):
                        st.json(args)
                elif name == "hybrid_search":
                    with st.expander(
                        f'Hybrid search — "{args.get("query", "")}"',
                        expanded=False,
                    ):
                        st.json(args)
                elif name in (
                    "write_file",
                    "edit_file",
                    "read_file",
                    "ls",
                    "glob",
                    "grep",
                ):
                    label = args.get("file_path") or args.get("path") or ""
                    with st.expander(
                        f"File system — {name} {label}", expanded=False
                    ):
                        st.json(args)
                else:
                    with st.expander(f"Tool — {name}", expanded=False):
                        st.json(args)
        elif msg_type == "tool":
            text = extract_text(msg.content)
            if len(text) > 700:
                text = text[:700] + " ...(truncated)"
            with st.expander(
                f"Result — {getattr(msg, 'name', 'tool')}", expanded=False
            ):
                st.code(text)


def render_files(files: dict):
    """Display virtual filesystem contents."""
    if not files:
        return
    with st.expander(f"Virtual files in workspace ({len(files)})", expanded=False):
        for path, data in sorted(files.items()):
            content = (
                data.get("content", "") if isinstance(data, dict) else str(data)
            )
            st.markdown(f"**`{path}`**")
            preview = content[:2000]
            if len(content) > 2000:
                preview += " ...(truncated)"
            st.code(preview)


# ---------------------------------------------------------------------------
# Agent factory for Streamlit (uses MemorySaver for in-process persistence)
# ---------------------------------------------------------------------------
def build_streamlit_agent(model: str):
    """Build the AuRA agent configured for the Streamlit session."""
    workspace = str(WORKSPACE_DIR)
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    backend = FilesystemBackend(root_dir=workspace, virtual_mode=True)

    agent = create_deep_agent(
        model=model,
        tools=ALL_TOOLS,
        system_prompt=ORCHESTRATOR_PROMPT,
        subagents=ALL_SUBAGENTS,
        backend=backend,
        checkpointer=st.session_state.checkpointer,
    )
    return agent


# ---------------------------------------------------------------------------
# Streamlit App
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AuRA — Autonomous Research Agent",
    page_icon="A",
    layout="wide",
)

# --- Custom styling ---
st.markdown(
    """
    <style>
    .stApp {
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    }
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #888;
        margin-bottom: 1.5rem;
    }
    div[data-testid="stExpander"] > details > summary {
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-header">AuRA</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    "Autonomous Research Agent &mdash; "
    "multi-agent research with ArXiv, Tavily, and Groq"
    "</div>",
    unsafe_allow_html=True,
)

# --- Session state init ---
if "checkpointer" not in st.session_state:
    st.session_state.checkpointer = MemorySaver()
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "history" not in st.session_state:
    st.session_state.history = []  # [(role, text, steps_messages, files)]

# --- Sidebar ---
with st.sidebar:
    st.header("Configuration")

    model = st.selectbox(
        "Model",
        [
            "groq:meta-llama/llama-4-scout-17b-16e-instruct",
            "groq:llama-3.3-70b-versatile",
            "groq:qwen/qwen3-32b",
        ],
        index=0,
        help="Select the Groq model for the orchestrator agent.",
    )

    st.divider()

    st.subheader("Session")
    thread_display = st.session_state.thread_id[:12] + "..."
    st.text(f"Thread: {thread_display}")

    col1, col2 = st.columns(2)
    if col1.button("New session", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.history = []
        st.rerun()
    if col2.button("Reset all", use_container_width=True):
        for k in ("checkpointer", "thread_id", "history"):
            st.session_state.pop(k, None)
        st.rerun()

    st.divider()

    st.subheader("System status")
    key_warnings = validate_keys()
    if not key_warnings:
        st.success("All API keys configured")
    else:
        for w in key_warnings:
            st.error(w)

    st.divider()

    st.subheader("Architecture")
    st.markdown(
        """
        **Orchestrator** decomposes queries and delegates to:

        - **Academic Synthesizer** — ArXiv papers
        - **Web Scraper** — Tavily web search
        - **Report Synthesizer** — final aggregation

        Data is offloaded to the Virtual Filesystem.
        State is persisted via SQL checkpointing.
        """
    )

# --- Build agent (rebuild on model change) ---
cfg_key = f"model={model}"
if st.session_state.get("cfg_key") != cfg_key:
    st.session_state.agent = build_streamlit_agent(model)
    st.session_state.cfg_key = cfg_key

# --- Replay chat history ---
for role, text, steps, files in st.session_state.history:
    with st.chat_message(role):
        if steps:
            render_steps(steps)
        st.markdown(text)
        if files:
            render_files(files)

# --- Chat input / agent invocation ---
if prompt := st.chat_input("Enter a research query..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.history.append(("user", prompt, None, None))

    payload = {"messages": [{"role": "user", "content": prompt}]}
    config = {
        "configurable": {"thread_id": st.session_state.thread_id},
        "recursion_limit": 100,
    }

    with st.chat_message("assistant"):
        with st.spinner("Researching — planning, searching, synthesising..."):
            try:
                result = st.session_state.agent.invoke(payload, config=config)
            except Exception as e:
                st.error(f"Agent error: {e}")
                st.stop()

        # Render only this turn's messages
        all_msgs = result["messages"]
        turn_start = max(
            (
                i
                for i, m in enumerate(all_msgs)
                if getattr(m, "type", "") == "human"
            ),
            default=0,
        )
        new_msgs = all_msgs[turn_start + 1 :]

        render_steps(new_msgs)
        answer = extract_text(all_msgs[-1].content) or "(no text response)"
        st.markdown(answer)

        # Virtual files
        files = result.get("files", {})
        render_files(files)

    st.session_state.history.append(("assistant", answer, new_msgs, files))
