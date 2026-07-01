"""
AuRA CLI entrypoint — run a research query from the command line.

Usage:
    python main.py "What are the latest advances in transformer efficiency?"
    python main.py --thread-id abc123   (resume a previous session)
    python main.py                      (interactive prompt)
"""

import argparse
import sys
import uuid

from aura.config import validate_keys


def main():
    parser = argparse.ArgumentParser(
        prog="aura",
        description="AuRA — Autonomous Research Agent (CLI)",
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Research query to investigate",
    )
    parser.add_argument(
        "--thread-id",
        default=None,
        help="Resume a previous research session by thread ID",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the default model (e.g. groq:llama-3.3-70b-versatile)",
    )
    args = parser.parse_args()

    # --- Validate API keys ---
    warnings = validate_keys()
    for w in warnings:
        print(f"[WARNING] {w}", file=sys.stderr)
    if any("GROQ_API_KEY" in w for w in warnings):
        print("[FATAL] Cannot proceed without GROQ_API_KEY.", file=sys.stderr)
        sys.exit(1)

    # --- Get query ---
    query = args.query
    if not query:
        print("AuRA — Autonomous Research Agent")
        print("-" * 40)
        query = input("Enter your research query: ").strip()
        if not query:
            print("No query provided. Exiting.")
            sys.exit(0)

    # --- Build agent ---
    # Import here so missing deps fail gracefully after arg parsing
    from aura.agent import create_aura_agent

    kwargs = {}
    if args.model:
        kwargs["model"] = args.model

    print(f"\n[AuRA] Initialising agent...")
    agent, checkpointer = create_aura_agent(**kwargs)

    # --- Configure session ---
    thread_id = args.thread_id or str(uuid.uuid4())
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 100,
    }

    print(f"[AuRA] Session: {thread_id}")
    print(f"[AuRA] Query: {query}")
    print(f"[AuRA] Researching...\n")

    # --- Invoke ---
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=config,
        )
    except KeyboardInterrupt:
        print("\n[AuRA] Interrupted. Session saved — resume with:")
        print(f"  python main.py --thread-id {thread_id}")
        sys.exit(0)
    except Exception as exc:
        print(f"\n[AuRA] Error: {exc}", file=sys.stderr)
        print(f"[AuRA] Session saved — resume with:")
        print(f"  python main.py --thread-id {thread_id}")
        sys.exit(1)

    # --- Output ---
    messages = result.get("messages", [])
    if messages:
        final = messages[-1]
        content = final.content if hasattr(final, "content") else str(final)
        if isinstance(content, list):
            # Handle content blocks
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block["text"])
                elif isinstance(block, str):
                    parts.append(block)
            content = "\n".join(parts)
        print("=" * 60)
        print("RESEARCH REPORT")
        print("=" * 60)
        print(content)
    else:
        print("[AuRA] No response generated.")

    # --- Show VFS files ---
    files = result.get("files", {})
    if files:
        print(f"\n{'=' * 60}")
        print(f"FILES IN WORKSPACE ({len(files)})")
        print("=" * 60)
        for path in sorted(files.keys()):
            print(f"  {path}")

    print(f"\n[AuRA] Session: {thread_id}")
    print(f"[AuRA] Resume with: python main.py --thread-id {thread_id}")


if __name__ == "__main__":
    main()
