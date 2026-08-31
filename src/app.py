"""Streamlit UI for the Tasklet support agent.

Run with:
    uv run streamlit run src/app.py

Layout:
  * Sidebar: pick which seed user to log in as, and a live table of that
    user's tickets (the table updates after every turn so students can
    see DB changes happen in real time).
  * Main panel: the chat with the agent. Each tool call and tool result
    is shown in a collapsible expander so the "thinking" of the agent
    is fully visible — this is a teaching feature.
  * "Reset conversation" wipes message history but keeps the conversation
    row (so resuming works on the next page load).

Notes for students:
  * Streamlit re-runs the entire script on every interaction. We re-open
    the SQLite connection and re-instantiate the Anthropic client each
    time. For a teaching demo this is fine.
  * The agent loop in src/agent.py does not know it is being driven from
    Streamlit. The same run_turn() function powers the CLI.
"""

import json
import os

import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv

from src.agent import run_turn
from src.conversation import Conversation
from src.db import get_connection
from src.models import AgentMessage, QueryFilters, ToolResult, ToolUse
from src.query_service import list_tickets

load_dotenv()

st.set_page_config(page_title="Tasklet Support", page_icon="🎫", layout="wide")

conn = get_connection()


def _render_message(msg: AgentMessage) -> None:
    """Render one message in the chat history."""
    if msg.role == "user":
        with st.chat_message("user", avatar="🙂"):
            st.write(msg.content)
    elif msg.role == "assistant":
        with st.chat_message("assistant", avatar="🎫"):
            if msg.content:
                st.write(msg.content)
            for tu in msg.tool_calls:
                with st.expander(f"🔧 Tool call: {tu.name}", expanded=False):
                    st.code(json.dumps(tu.input, indent=2), language="json")
    elif msg.role == "tool":
        tr = msg.tool_result
        label = "📦 Tool result" + (" (error)" if tr and tr.is_error else "")
        with st.expander(label, expanded=False):
            content = tr.content if tr else ""
            try:
                pretty = json.dumps(json.loads(content), indent=2)
                st.code(pretty, language="json")
            except json.JSONDecodeError:
                st.write(content)


# ---------- sidebar: user selection + live ticket table ----------

users = conn.execute("SELECT id, name, email FROM users ORDER BY id").fetchall()
if not users:
    st.error(
        "No seed users found. Run `uv run python3 main.py --init-db` first, "
        "then reload this page."
    )
    st.stop()

with st.sidebar:
    st.title("Tasklet Support")
    options = {f"{u['name']} (id {u['id']})": u["id"] for u in users}
    chosen_label = st.selectbox("Logged in as", list(options.keys()))
    user_id = options[chosen_label]

    if st.button("Reset conversation", use_container_width=True):
        if "conversation" in st.session_state:
            st.session_state.conversation.reset()
        st.rerun()

    st.divider()
    st.subheader("Your tickets")
    tickets = list_tickets(conn, user_id, QueryFilters())
    if tickets:
        st.caption(f"{len(tickets)} total — newest first")
        st.dataframe(
            [
                {
                    "id": t.id,
                    "priority": t.priority.value,
                    "created": t.created_at.strftime("%Y-%m-%d"),
                    "status": t.status.value,
                    "title": t.title,
                }
                for t in tickets
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.write("No tickets yet.")


# ---------- main panel: chat ----------

if (
    "conversation" not in st.session_state
    or st.session_state.get("active_user_id") != user_id
):
    st.session_state.conversation = Conversation.load_or_create(conn, user_id)
    st.session_state.active_user_id = user_id

conversation: Conversation = st.session_state.conversation

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    st.error(
        "ANTHROPIC_API_KEY is not set. Add it to .env and restart Streamlit."
    )
    st.stop()

client = Anthropic(api_key=api_key)

st.title(f"👋 Hi, {chosen_label.split(' (')[0]}")
st.caption(
    "Ask the support agent to look up your tickets or file a new one. "
    "Tool calls are shown inline so you can see exactly what the agent did."
)

for msg in conversation.messages:
    _render_message(msg)


def _on_tool_call(_tu: ToolUse, _tr: ToolResult) -> None:
    # The full tool call and result are persisted to the DB inside run_turn,
    # so we render them on the next script run via _render_message. Nothing
    # to do here for now — the callback exists so the CLI can use it for
    # --verbose output without changing the agent loop.
    pass


if prompt := st.chat_input("Ask the support agent..."):
    with st.spinner("Thinking..."):
        try:
            run_turn(
                client=client,
                conn=conn,
                conversation=conversation,
                user_input=prompt,
                on_tool_call=_on_tool_call,
            )
        except Exception as e:  # noqa: BLE001
            st.error(f"{type(e).__name__}: {e}")
    st.rerun()
