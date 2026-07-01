# AuRA — Autonomous Research Agent

A multi-agent research system built on **LangChain deepagents**, designed to
automate complex, multi-step technical research.  AuRA decomposes broad
research queries, delegates work to specialised subagents, and produces
comprehensive, source-cited research reports.

## Architecture

```
User Query
    |
    v
Orchestrator Agent (Groq)
    |
    |-- write_todos       -->  Plan research steps
    |-- academic-synthesizer  -->  ArXiv papers
    |-- web-scraper           -->  Tavily web search
    |-- report-synthesizer    -->  Final report
    |
    |-- Virtual Filesystem (workspace/)
    |     raw/     <-- raw paper text, web data
    |     notes/   <-- synthesised notes
    |     reports/ <-- final reports
    |
    |-- SQL Checkpointer (aura_state.db)
```

### Key Components

| Component | Technology | Purpose |
|---|---|---|
| LLM Provider | Groq (qwen3-32b) | Ultra-low latency reasoning |
| Agent Framework | deepagents + LangGraph | Multi-agent orchestration |
| Persistence | SQLite (SqliteSaver) | Session state checkpointing |
| Context Management | FilesystemBackend VFS | Context window offloading |
| Academic Search | ArXiv API | Peer-reviewed literature |
| Web Search | Tavily API | Real-time web intelligence |

## Setup

### 1. Install dependencies

```bash
cd Researchagent
pip install -e .
# or
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and add your keys:
#   GROQ_API_KEY=...
#   TAVILY_API_KEY=...
```

### 3. Run

**CLI:**
```bash
python main.py "What are the latest advances in transformer efficiency?"
```

**Resume a session:**
```bash
python main.py --thread-id <session-id>
```

**Streamlit UI:**
```bash
streamlit run app.py
```

## Project Structure

```
Researchagent/
├── .env.example           # API key template
├── README.md
├── pyproject.toml         # Dependencies
├── requirements.txt
├── main.py                # CLI entrypoint
├── app.py                 # Streamlit UI
├── aura/
│   ├── __init__.py
│   ├── config.py          # Environment and constants
│   ├── tools.py           # ArXiv + Tavily + hybrid search
│   ├── schemas.py         # Pydantic output models
│   ├── subagents.py       # Subagent definitions
│   ├── agent.py           # Main agent factory
│   └── context/
│       └── AGENTS.md      # Agent context file
└── workspace/             # Virtual filesystem root
    ├── raw/               # Raw data dumps
    ├── notes/             # Synthesised notes
    └── reports/           # Final reports
```

## How It Works

1. **Planning**: The orchestrator uses `write_todos` to decompose your query
   into discrete research tasks.

2. **Academic Research**: The `academic-synthesizer` subagent searches ArXiv
   for peer-reviewed papers, extracting titles, authors, abstracts, and URLs.

3. **Web Research**: The `web-scraper` subagent searches Tavily for current
   implementations, blog posts, news, and documentation.

4. **Context Offloading**: Raw data is written to the VFS (`workspace/`)
   rather than kept in the conversation, keeping the LLM context lean.

5. **Checkpointing**: State is persisted to SQLite at every graph node
   transition, enabling session resumption after interrupts.

6. **Synthesis**: The `report-synthesizer` reads all VFS notes and produces
   a final Markdown report with cross-referenced findings, confidence
   scores, and full source citations.

## License

MIT
