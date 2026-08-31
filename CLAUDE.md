# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## What this project is

A multi-turn AI support agent for the fictional SaaS "Tasklet", built directly on
the Anthropic Claude API with native tool use and no agent framework. The agent
exposes three tools — `create_ticket`, `list_tickets`, `get_ticket_by_id` — over
one Python core with two interchangeable UIs (CLI and Streamlit).

The codebase is deliberately small and readable: every file is meant to be
followed top to bottom without jumping through layers of abstraction.

## Common commands

```bash
# install (first time)
uv sync --extra dev
cp .env.example .env        # add ANTHROPIC_API_KEY

# database (destructive: wipes + reseeds)
uv run python main.py --init-db

# run a UI
uv run python main.py --user-id 1 --verbose   # CLI, prints every tool call
uv run streamlit run src/app.py               # Streamlit (port 8501)

# tests
uv run pytest                                               # full suite
uv run pytest -k security                                   # just the security tests
uv run pytest tests/test_agent.py::test_run_turn_caps_tool_calls   # one test
```

With the venv activated (`source .venv/bin/activate`) the CLI is just
`python main.py ...`.

## Architecture

The agent core is a small set of Python modules. Both UIs drive the same core; do not duplicate logic into a UI layer.

```
          CLI (main.py) ──┐
     Streamlit (app.py) ──┴──> agent.run_turn ──> tools.dispatch ──> {ticket,query}_service ──> sqlite
```

- **agent.py** owns the loop: append user message → call Claude → if tool_use, dispatch and append result, loop → return final text. Hard cap of 5 tool calls per turn. The system prompt is sent as a cache-controlled block (`cache_control: ephemeral`) so it and the tool schemas are reused from the prompt cache across turns.
- **tools.py** owns *both* the JSON tool schemas Claude sees and the `dispatch()` function that routes a `ToolUse` to the right service. Tool descriptions in this file are some of the most behavior-influential prompts in the system — when changing agent behavior, edit them before touching code.
- **conversation.py** owns persistence and the conversion between our internal three-role message log (`user`/`assistant`/`tool`) and Anthropic's two-role API shape. The `tool` role collapses to `user` + `tool_result` block at the API boundary.
- **prompts.py** holds `MODEL` and `SYSTEM_PROMPT`. The model id is pinned — update it deliberately, not via "-latest" aliases.
- **app.py** is the Streamlit UI — a thin layer over `agent.run_turn`. It must not contain agent logic; that belongs in agent.py / tools.py / a service.

### The security invariant

This is the single most important rule in the codebase, and it spans multiple files:

1. The LLM never sees `user_id` in any tool schema in [src/tools.py](src/tools.py).
2. `dispatch()` never reads `user_id` from `tool_use.input` — it uses the `user_id` parameter the caller passed in. Pydantic v2's default `extra="ignore"` also drops a stray `user_id` field, but dispatch is the load-bearing layer.
3. Every function in [src/ticket_service.py](src/ticket_service.py) and [src/query_service.py](src/query_service.py) takes `user_id` as the **first required parameter**. There is no overload that accepts only a `ticket_id`. Do not add one.
4. `get_ticket_by_id` returns the same `None` whether the ticket doesn't exist OR belongs to another user. Do not "improve" the error message — the indistinguishability is intentional, to prevent existence leaks.

The three SECURITY-labeled tests in [tests/test_tool_dispatch.py](tests/test_tool_dispatch.py) prove (1)–(3). Do not delete or weaken them.

## Design constraints

Deliberate decisions, not historical accidents:

- **No agent frameworks.** No LangChain, LlamaIndex, CrewAI, AutoGen. Direct Anthropic SDK with native tool use only.
- **No ORM.** Raw `sqlite3` with parameterized SQL only, so the SQL and the security model stay visible.
- **No LLM-generated SQL.** The LLM picks among pre-defined query functions via tool use. A "free-form query" tool would be a regression.
- **Sequential tool use.** The system prompt instructs Claude to issue one tool call per turn; the agent loop handles the general case defensively.
- **Three tools.** `create_ticket`, `list_tickets`, `get_ticket_by_id`. The agent is specified to refuse `update_ticket` / `delete_ticket` requests.
- **No mocking the database in tests.** Tests use an in-memory SQLite from the same `schema.sql` — real DB behavior, no mock-vs-prod drift.

## Things that look wrong but aren't

- **`check_same_thread=False`** in [src/db.py](src/db.py) is required for Streamlit. SQLite is single-writer; this app has one user per process.
- **Custom `register_adapter`/`register_converter` for datetime** in [src/db.py](src/db.py) is required because Python 3.12 deprecated and 3.14 removed the implicit defaults. Removing them breaks `Ticket(**row)` parsing.
- **`messages.content` is a JSON blob**, not a relational structure. The conversation log is an append-only event stream and is never queried into.
- **CHECK constraints duplicate the Pydantic enums.** Defense in depth, on purpose.
- **`agent.run_turn` re-prompts even when Claude returns text + tool_use simultaneously.** Correct: if there are tool_uses, the loop runs them and continues; the text from that turn is preserved in the assistant message.

## Testing notes

- No live API calls. [tests/test_agent.py](tests/test_agent.py) uses a tiny ducktyped fake Anthropic client — keep it tiny.
- [tests/conftest.py](tests/conftest.py) provides an in-memory `conn` fixture, plus `seed_users` and `seed_tickets` (a 7-ticket controlled dataset, distinct from `data/seed.sql`'s 100-ticket demo data).
- Routing behavior (does Claude pick the right tool for a given prompt?) is verified interactively via the demo walkthrough in [README.md](README.md), not in pytest. Do not add a test that requires a live API key to CI.
