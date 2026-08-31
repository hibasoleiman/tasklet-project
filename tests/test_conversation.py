"""Tests for the Conversation class — persistence and shape conversion."""

from src.conversation import Conversation
from src.models import AgentMessage, ToolResult, ToolUse


def test_load_or_create_creates_new_conversation(conn, seed_users):
    conv = Conversation.load_or_create(conn, user_id=1)
    assert conv.user_id == 1
    assert conv.messages == []
    assert conv.id is not None

    row = conn.execute(
        "SELECT user_id FROM conversations WHERE id = ?", (conv.id,)
    ).fetchone()
    assert row["user_id"] == 1


def test_appended_messages_persist_across_loads(conn, seed_users):
    conv = Conversation.load_or_create(conn, user_id=1)
    conv.append(AgentMessage(role="user", content="hello"))

    reloaded = Conversation.load_or_create(conn, user_id=1)
    assert reloaded.id == conv.id
    assert len(reloaded.messages) == 1
    assert reloaded.messages[0].content == "hello"


def test_load_or_create_returns_most_recent_for_user(conn, seed_users):
    Conversation.new(conn, user_id=1)
    second = Conversation.new(conn, user_id=1)

    loaded = Conversation.load_or_create(conn, user_id=1)
    assert loaded.id == second.id


def test_new_starts_fresh_even_when_one_exists(conn, seed_users):
    first = Conversation.load_or_create(conn, user_id=1)
    first.append(AgentMessage(role="user", content="old"))

    second = Conversation.new(conn, user_id=1)
    assert second.id != first.id
    assert second.messages == []


def test_reset_clears_messages_but_keeps_conversation(conn, seed_users):
    conv = Conversation.load_or_create(conn, user_id=1)
    conv.append(AgentMessage(role="user", content="msg1"))
    conv.append(AgentMessage(role="user", content="msg2"))

    conv.reset()
    assert conv.messages == []

    reloaded = Conversation.load_or_create(conn, user_id=1)
    assert reloaded.id == conv.id
    assert reloaded.messages == []


def test_to_anthropic_messages_collapses_tool_role_to_user(conn, seed_users):
    """Anthropic uses 'user' role for tool_results. Test the collapse."""
    conv = Conversation.load_or_create(conn, user_id=1)
    conv.append(AgentMessage(role="user", content="show me my tickets"))
    conv.append(
        AgentMessage(
            role="assistant",
            content=None,
            tool_calls=[ToolUse(id="t1", name="list_tickets", input={})],
        )
    )
    conv.append(
        AgentMessage(
            role="tool",
            tool_result=ToolResult(
                tool_use_id="t1", content="[]", is_error=False
            ),
        )
    )

    msgs = conv.to_anthropic_messages()
    assert len(msgs) == 3
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "show me my tickets"

    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["content"][0]["type"] == "tool_use"
    assert msgs[1]["content"][0]["name"] == "list_tickets"

    assert msgs[2]["role"] == "user"  # collapsed from 'tool'
    assert msgs[2]["content"][0]["type"] == "tool_result"
    assert msgs[2]["content"][0]["tool_use_id"] == "t1"


def test_to_anthropic_messages_includes_assistant_text(conn, seed_users):
    conv = Conversation.load_or_create(conn, user_id=1)
    conv.append(
        AgentMessage(
            role="assistant",
            content="Here are your tickets:",
            tool_calls=[],
        )
    )
    msgs = conv.to_anthropic_messages()
    assert msgs[0]["role"] == "assistant"
    assert msgs[0]["content"][0]["type"] == "text"
    assert msgs[0]["content"][0]["text"] == "Here are your tickets:"


def test_isolated_per_user(conn, seed_users):
    """User 1 and user 2 each get their own conversation row."""
    c1 = Conversation.load_or_create(conn, user_id=1)
    c2 = Conversation.load_or_create(conn, user_id=2)
    assert c1.id != c2.id

    c1.append(AgentMessage(role="user", content="user 1 message"))

    reloaded2 = Conversation.load_or_create(conn, user_id=2)
    assert reloaded2.messages == []
