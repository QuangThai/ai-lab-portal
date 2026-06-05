"""Seed two blog posts via the admin API using content from test-post.md."""

import json
import sys
from time import time
from urllib.request import Request, urlopen
from urllib.error import URLError

# Add backend to path so we can import the signing function
sys.path.insert(0, "D:/Personal/ai-lab-portal/backend")
from backend.app.admin_boundary import sign_admin_identity

BACKEND_URL = "http://127.0.0.1:18000"
SECRET = "ai-lab-dev-boundary-2026-secret!"


def admin_headers() -> dict[str, str]:
    payload = json.dumps(
        {
            "user_id": "user_admin_1",
            "email": "admin@ai-lab.local",
            "role": "admin",
            "issued_at": int(time()),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return {
        "x-ai-lab-admin-identity": payload,
        "x-ai-lab-admin-signature": sign_admin_identity(payload, SECRET),
    }


def api_call(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{BACKEND_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = Request(url, data=data, method=method)
    for k, v in admin_headers().items():
        req.add_header(k, v)
    req.add_header("Content-Type", "application/json")
    try:
        resp = urlopen(req)
        return json.loads(resp.read().decode())
    except URLError as e:
        body_text = e.read().decode() if hasattr(e, "read") else str(e)
        print(f"  ! API error {method} {path}: {e.code if hasattr(e, 'code') else ''} {body_text[:200]}")
        raise


# ──────────────────────────────────────────────
# Post 1: "Extending Your Pi Agent Workflow"
# ──────────────────────────────────────────────

post1_payload = {
    "slug": "extending-pi-agent-workflow",
    "title": "Extending Your Pi Agent Workflow: A Guide to Essential Packages",
    "excerpt": (
        "Pi's ecosystem of packages and extensions unlocks everything from subagent orchestration "
        "and task management to memory persistence, MCP integration, guardrails, and more. "
        "Here is a curated tour of the most valuable tools for serious Pi users."
    ),
    "author_name": "AI Lab Team",
    "author_user_id": "user_admin_1",
    "content_markdown": (
        "## Supercharge Your Pi Agent with the Right Extensions\n\n"
        "Pi is a powerful agent harness on its own, but its true potential shines when you layer in the ecosystem of community packages built around it. "
        "These extensions bring subagent orchestration, persistent memory, task tracking, MCP connectivity, guardrails, and richer tool output — transforming Pi from a capable assistant into a full-blown agent platform.\n\n"
        "Below is a curated tour of the most valuable packages for serious Pi users, grouped by capability.\n\n"
        "---\n\n"
        "### Subagents & Task Management\n\n"
        "**Subagents** ([`@tintinweb/pi-subagents`](https://www.npmjs.com/package/@tintinweb/pi-subagents)) lay the foundation: they let Pi spawn and coordinate child agents to decompose complex work into parallel, focused subtasks. Each subagent runs in its own context with a clear objective, making it ideal for research, code generation, or any multi-step workflow.\n\n"
        "For tracking progress at a glance, **Tasks** ([`@tintinweb/pi-tasks`](https://www.npmjs.com/package/@tintinweb/pi-tasks)) provides a structured todo list that Pi updates as work proceeds. Instead of relying on free-form context, each task has a status, owner, and description — giving both you and the agent a shared view of what has been done and what comes next.\n\n"
        "---\n\n"
        "### Persistent Context: Memory & MCP\n\n"
        "One of Pi's most requested features — remembering context between sessions — is delivered by **Memory Markdown** ([`pi-memory-md`](https://www.npmjs.com/package/pi-memory-md)). It stores durable knowledge (project conventions, user preferences, recurring patterns) as Markdown files in a lightweight git-backed repository. The result: Pi can recall what it learned last week without re-reading your entire codebase.\n\n"
        "To bridge Pi with external tools, the **MCP Adapter** ([`pi-mcp-adapter`](https://www.npmjs.com/package/pi-mcp-adapter)) connects the agent to any MCP-compatible server — databases, APIs, file systems, or custom services. This effectively unbundles Pi's tooling surface from its core, letting you plug in exactly the capabilities your workflow requires.\n\n"
        "---\n\n"
        "### Safety, Control & Transparency\n\n"
        "When running autonomous agents at scale, **Guardrails** ([`@aliou/pi-guardrails`](https://www.npmjs.com/package/@aliou/pi-guardrails)) adds an essential safety layer: configurable rules that constrain agent behavior, enforce boundaries, and prevent unintended actions.\n\n"
        "**Tool Display** ([`pi-tool-display`](https://www.npmjs.com/package/pi-tool-display)) improves the visibility of what your agent is actually doing. Instead of raw tool-call logs, you get a formatted, readable view of each operation and its result — invaluable for debugging and trust.\n\n"
        "For deeper workflow hooks, **Augment** ([`pi-augment`](https://www.npmjs.com/package/pi-augment)) provides an augmentation framework that lets you inject custom logic at key points in Pi's execution cycle. And **Multi-pass** ([`github.com/hjanuschka/pi-multi-pass`](https://github.com/hjanuschka/pi-multi-pass)) runs repeated processing passes to iteratively improve output quality.\n\n"
        "---\n\n"
        "### Interaction & Workflow Enhancements\n\n"
        "**BTW** ([`github.com/dbachelder/pi-btw`](https://github.com/dbachelder/pi-btw)) is a lightweight utility that injects contextual nudges during agent runs — perfect for reminding Pi of conventions mid-task without breaking flow.\n\n"
        "**Ask User Question** ([`github.com/ghoseb/pi-askuserquestion`](https://github.com/ghoseb/pi-askuserquestion)) gives the agent explicit permission to clarify ambiguities with you instead of guessing — a small change that dramatically improves output reliability.\n\n"
        "**VCC** ([`@sting8k/pi-vcc`](https://www.npmjs.com/package/@sting8k/pi-vcc)) adds control and coordination mechanisms worth exploring if you run multi-agent pipelines.\n\n"
        "**Agent Modes** ([`@danchamorro/pi-agent-modes`](https://www.npmjs.com/package/@danchamorro/pi-agent-modes)) lets you switch Pi between operational modes (e.g., fast mode vs. thorough mode) depending on the task type — routing different kinds of work through the right configuration automatically.\n\n"
        "And **Amp-like** ([`pi-amplike`](https://www.npmjs.com/package/pi-amplike)) brings an Amp-inspired permission workflow to Pi. Since Pi defaults to YOLO mode, installing this adds `/permission` gates, `/handoff`, and `/query-thread` — giving you fine-grained control over autonomous execution.\n\n"
        "---\n\n"
        "### Quick Start with LazyPi\n\n"
        "If you are new to Pi's extension ecosystem, [**LazyPi**](https://lazypi.org/) bundles the most useful packages into a single, opinionated starter kit. It is the fastest way to get a fully-featured environment without manually assembling each piece. Once you outgrow it, you can swap individual packages to match your exact needs.\n\n"
        "For Cursor users, the [**Pi Cursor SDK**](https://pi.dev/packages/pi-cursor-sdk) lets you experience Pi's extended workflow directly inside the Cursor editor.\n\n"
        "---\n\n"
        "_Start with what you need. Add as you grow. That is the beauty of Pi's modular ecosystem._"
    ),
    "image_url": None,
}

# ──────────────────────────────────────────────
# Post 2: "Ten Pro Tips for Mastering Codex"
# ──────────────────────────────────────────────

post2_payload = {
    "slug": "mastering-codex-cli-pro-tips",
    "title": "Ten Pro Tips for Mastering Codex CLI",
    "excerpt": (
        "Small workflow habits make a big difference in Codex — from extending context lifetime "
        "and controlling session scope to batching tool calls and scaling with multi-agent. "
        "Here are ten battle-tested tips from months of daily use."
    ),
    "author_name": "AI Lab Team",
    "author_user_id": "user_admin_1",
    "content_markdown": (
        "After spending months with Codex CLI day in and day out, a few patterns emerged that "
        "dramatically improved context durability, session controllability, and the ability to scale work with agents and skills. "
        "Here are ten tips worth integrating into your daily practice.\n\n"
        "---\n\n"
        "#### 1. Turn Off Fast Mode for Long Tasks\n\n"
        "Fast mode (`/fast`) is convenient when you need quick responses, but for long-running tasks "
        "with many tool calls or deep reasoning, disable it (`/fast off`). The stability and quality "
        "gains far outweigh the slight speed trade-off. Fast mode works best for simple lookups; "
        "everything else deserves the full reasoning pipeline.\n\n"
        "#### 2. Use `/side` for Side Questions\n\n"
        "When you are deep in a main task and a related question comes up, use `/side` to open a "
        "side conversation instead of polluting your main context. It works like `/btw` in Claude Code — "
        "a detached transcript that does not interfere with the parent thread. When the side question "
        "is resolved, you return to your original context intact.\n\n"
        "#### 3. Double-Tap Escape to Rewind\n\n"
        "If Codex heads down the wrong path, press **Esc** twice to rewind and rollback. This is your "
        "emergency brake: rather than typing corrective instructions on a wrong branch, rewind to the "
        "last good state and re-steer the prompt. It saves time and keeps the transcript clean.\n\n"
        "#### 4. Use `$` to Trigger Skills\n\n"
        "Triggering a skill with `$skill-name` is often more convenient than a slash command. The `$` "
        "prefix cleanly separates skill invocations from session-control commands like `/model`, `/fast`, "
        "or `/agent`, reducing ambiguity and keeping your inputs organized.\n\n"
        "#### 5. Enable Long-Term Memory\n\n"
        "If you want Codex to remember context across sessions, turn on memories. This requires enabling "
        "both the feature flag and the memory behavior:\n\n"
        "```toml\n"
        "[features]\n"
        "memories = true\n\n"
        "[memories]\n"
        "generate_memories = true\n"
        "use_memories = true\n"
        "```\n\n"
        "Memories are excellent for user preferences, repository conventions, and lessons learned. "
        "Do not expect them to replace reading the current source — they complement, not substitute, "
        "context from the active session.\n\n"
        "#### 6. Scale with Multi-Agent\n\n"
        "Codex's multi-agent system runs agents in parallel threads, each at the same level as the main agent. "
        "Use `/agent` to switch between threads. Configure limits in your config:\n\n"
        "```toml\n"
        "[agents]\n"
        "max_depth = 1\n"
        "max_threads = 12\n"
        "```\n\n"
        "`max_threads` controls how many agents can run concurrently; `max_depth` controls how deep "
        "agents can spawn sub-agents. Combined with MCP and specialized skills, this is extremely powerful — "
        "as long as each task has a clear owner and well-defined output.\n\n"
        "#### 7. Embed Codex as an MCP Server\n\n"
        "Codex CLI can run as an MCP server, meaning you can embed it into another agent's workflow. "
        "For example, Agents SDK can call Codex via MCP to start or continue conversations. This opens "
        "the door to deterministic multi-agent pipelines where Codex handles specific sub-tasks within "
        "a larger orchestration framework.\n\n"
        "#### 8. Automate Lifecycles with Hooks\n\n"
        "Codex hooks are stable enough now to serve as production-grade lifecycle automation. Configure "
        "them in `hooks.json` or inline `[hooks]` in your config, and enable with `features.hooks = true`. "
        "They work well for notifications, guardrails, workflow checks, and log/evidence automation — "
        "replacing ad-hoc scripts with structured lifecycle callbacks.\n\n"
        "#### 9. Use the JS REPL for Batch Operations\n\n"
        "Enable the JavaScript REPL (`features.js_repl = true`) when you need to batch tool calls, "
        "parse outputs, manipulate data, or transform JSON and CSV quickly within the session. It is "
        "surprisingly useful for consolidating multiple outputs, filtering datasets, performing quick "
        "calculations, and normalizing payloads before feeding them back to the agent.\n\n"
        "#### 10. Use `/goal` with Caution\n\n"
        "Codex's `/goal` feature is useful for maintaining a long-running objective within a thread, "
        "but it is still experimental and can be token-intensive. Enable it explicitly:\n\n"
        "```toml\n"
        "[features]\n"
        "goals = true\n"
        "```\n\n"
        "Use `/goal` when you need Codex to remember a persistent objective across many turns. "
        "Just keep an eye on token burn — and consider whether a structured task breakdown or "
        "multi-agent approach might achieve the same result more efficiently.\n\n"
        "---\n\n"
        "### Bonus Tips\n\n"
        "- **Compact regularly**: Run `/compact` after each milestone, not just when context is about to overflow. A compacted context helps the agent retain the signal without dragging along stale noise.\n"
        "- **Check `/status` often**: When the agent behaves oddly, the first step is `/status` — verify the model, permissions, writable roots, and token usage. The cause is often a wrong mode or missing permission.\n"
        "- **Run `/diff` before asking for edits**: It shows the exact blast radius of current changes, especially important when a worktree already has edits from another agent or a human.\n"
        "- **Verify MCP tools with `/mcp verbose`**: A configured plugin does not guarantee the runtime exposes its tools. Always verify.\n"
        "- **Keep persistent config in `~/.codex/config.toml`**: Repo-specific behavior belongs in a project-level `.codex/config.toml`. Avoid relying on command-line overrides for long-term preferences.\n"
        "- **Divide large tasks clearly**: The main agent handles orchestration; subagents handle independent work with well-defined outputs that do not touch the same files.\n\n"
        "_Small habits, repeated daily, compound into a dramatically smoother Codex experience._"
    ),
    "image_url": None,
}


def main():
    import os
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace") if hasattr(sys.stdout, "reconfigure") else None
    # Post 1
    print("Creating Post 1: 'Extending Your Pi Agent Workflow' ...", end=" ")
    try:
        result = api_call("POST", "/admin/blog-posts", post1_payload)
        post1_id = result["id"]
        print(f"✓ draft created (id={post1_id})")
    except Exception as e:
        print(f"✗ failed: {e}")
        # Try creating the post via publish -> draft directly
        return

    # Publish Post 1
    print(f"  Publishing Post 1 ...", end=" ")
    try:
        api_call("POST", f"/admin/blog-posts/{post1_id}/publish")
        print("✓ published")
    except Exception as e:
        print(f"✗ failed: {e}")

    # Post 2
    print("Creating Post 2: 'Ten Pro Tips for Mastering Codex CLI' ...", end=" ")
    try:
        result = api_call("POST", "/admin/blog-posts", post2_payload)
        post2_id = result["id"]
        print(f"✓ draft created (id={post2_id})")
    except Exception as e:
        print(f"✗ failed: {e}")
        return

    # Publish Post 2
    print(f"  Publishing Post 2 ...", end=" ")
    try:
        api_call("POST", f"/admin/blog-posts/{post2_id}/publish")
        print("✓ published")
    except Exception as e:
        print(f"✗ failed: {e}")

    print("\nDone! Both posts are published.")
    print(f"  → /blog/extending-pi-agent-workflow")
    print(f"  → /blog/mastering-codex-cli-pro-tips")


if __name__ == "__main__":
    main()
