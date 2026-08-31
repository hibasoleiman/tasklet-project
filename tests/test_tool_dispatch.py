"""Tests for the tool dispatch layer.

dispatch() is the bridge between the LLM and the service layer. The most
important tests in this file are the SECURITY tests proving that dispatch
ignores any user_id the LLM tries to inject and instead uses the
authenticated user_id passed in by the caller.
"""

import json

from src.models import ToolUse
from src.tools import TOOL_SCHEMAS, dispatch


# ---------- routing ----------

def test_dispatch_routes_create_ticket(conn, seed_users):
    tu = ToolUse(
        id="t1",
        name="create_ticket",
        input={
            "title": "Login button greyed out",
            "description": "Cannot log in.",
            "category": "bug_report",
            "priority": "high",
        },
    )
    result = dispatch(conn, user_id=1, tool_use=tu)

    assert result.tool_use_id == "t1"
    assert result.is_error is False
    payload = json.loads(result.content)
    assert payload["user_id"] == 1
    assert payload["title"] == "Login button greyed out"
    assert payload["status"] == "open"


def test_dispatch_routes_list_tickets_no_filter(conn, seed_tickets):
    tu = ToolUse(id="t1", name="list_tickets", input={})
    result = dispatch(conn, user_id=1, tool_use=tu)

    assert result.is_error is False
    payload = json.loads(result.content)
    assert payload["count"] == 5
    assert all(t["user_id"] == 1 for t in payload["tickets"])


def test_dispatch_routes_list_tickets_with_filter(conn, seed_tickets):
    tu = ToolUse(id="t1", name="list_tickets", input={"status": "open"})
    result = dispatch(conn, user_id=1, tool_use=tu)

    payload = json.loads(result.content)
    assert payload["count"] == 1
    assert payload["tickets"][0]["title"] == "Alpha bug"


def test_dispatch_routes_get_ticket_found(conn, seed_tickets):
    user1_id = conn.execute(
        "SELECT id FROM tickets WHERE user_id = 1 LIMIT 1"
    ).fetchone()["id"]
    tu = ToolUse(
        id="t1", name="get_ticket_by_id", input={"ticket_id": user1_id}
    )
    result = dispatch(conn, user_id=1, tool_use=tu)

    payload = json.loads(result.content)
    assert payload["found"] is True
    assert payload["ticket"]["user_id"] == 1


def test_dispatch_routes_get_ticket_not_found(conn, seed_tickets):
    """Asking for a non-existent ticket is NOT a tool error — the LLM still
    gets a successful response saying 'found: false', and can phrase that
    naturally to the user.
    """
    tu = ToolUse(id="t1", name="get_ticket_by_id", input={"ticket_id": 99999})
    result = dispatch(conn, user_id=1, tool_use=tu)

    assert result.is_error is False
    payload = json.loads(result.content)
    assert payload["found"] is False


# ---------- error handling ----------

def test_dispatch_unknown_tool_name(conn, seed_users):
    tu = ToolUse(id="t1", name="delete_all_tickets", input={})
    result = dispatch(conn, user_id=1, tool_use=tu)

    assert result.is_error is True
    assert "Unknown tool" in result.content


def test_dispatch_validation_error_round_trips(conn, seed_users):
    """Bad enum from the LLM → ToolResult with is_error=True and a useful
    message, so the agent loop can feed it back to Claude for self-correction.
    """
    tu = ToolUse(
        id="t1",
        name="create_ticket",
        input={
            "title": "x",
            "description": "x",
            "category": "not_a_category",
            "priority": "low",
        },
    )
    result = dispatch(conn, user_id=1, tool_use=tu)

    assert result.is_error is True
    assert "validation" in result.content.lower()


def test_dispatch_missing_required_field(conn, seed_users):
    tu = ToolUse(
        id="t1",
        name="create_ticket",
        input={"title": "x"},  # missing description/category/priority
    )
    result = dispatch(conn, user_id=1, tool_use=tu)
    assert result.is_error is True


def test_dispatch_get_ticket_missing_id(conn, seed_users):
    tu = ToolUse(id="t1", name="get_ticket_by_id", input={})
    result = dispatch(conn, user_id=1, tool_use=tu)
    assert result.is_error is True


def test_dispatch_get_ticket_wrong_type_id(conn, seed_users):
    tu = ToolUse(id="t1", name="get_ticket_by_id", input={"ticket_id": "abc"})
    result = dispatch(conn, user_id=1, tool_use=tu)
    assert result.is_error is True


# ---------- security ----------

def test_security_llm_user_id_in_create_is_ignored(conn, seed_users):
    """SECURITY: LLM tries to inject user_id=2 while the session is user 1.
    The created ticket must end up owned by user 1, and user 2 must remain
    untouched.
    """
    tu = ToolUse(
        id="t1",
        name="create_ticket",
        input={
            "title": "Injected",
            "description": "LLM tried to set user_id=2",
            "category": "bug_report",
            "priority": "low",
            "user_id": 2,  # the attempted injection
        },
    )
    result = dispatch(conn, user_id=1, tool_use=tu)

    assert result.is_error is False
    payload = json.loads(result.content)
    assert payload["user_id"] == 1, "dispatch must use session user_id, not LLM-supplied"

    user2_count = conn.execute(
        "SELECT COUNT(*) AS n FROM tickets WHERE user_id = 2"
    ).fetchone()["n"]
    assert user2_count == 0


def test_security_llm_user_id_in_list_is_ignored(conn, seed_tickets):
    """SECURITY: LLM tries to list tickets for user 2 while session is user 1.
    Result must contain only user 1's tickets.
    """
    tu = ToolUse(id="t1", name="list_tickets", input={"user_id": 2})
    result = dispatch(conn, user_id=1, tool_use=tu)

    payload = json.loads(result.content)
    assert payload["count"] == 5, "user 1 has 5 tickets in the fixture"
    assert all(t["user_id"] == 1 for t in payload["tickets"])


def test_security_get_other_users_ticket_returns_not_found(conn, seed_tickets):
    """SECURITY: requesting user 2's ticket from a user 1 session looks
    indistinguishable from requesting a non-existent id — both return
    found=False, never the underlying ticket.
    """
    user2_id = conn.execute(
        "SELECT id FROM tickets WHERE user_id = 2 LIMIT 1"
    ).fetchone()["id"]
    tu = ToolUse(
        id="t1", name="get_ticket_by_id", input={"ticket_id": user2_id}
    )
    result = dispatch(conn, user_id=1, tool_use=tu)

    payload = json.loads(result.content)
    assert payload["found"] is False


# ---------- schema sanity ----------

def test_tool_schemas_have_required_anthropic_fields():
    """Catch typos: every Anthropic tool schema needs name, description, input_schema."""
    assert len(TOOL_SCHEMAS) == 3
    names = {s["name"] for s in TOOL_SCHEMAS}
    assert names == {"create_ticket", "list_tickets", "get_ticket_by_id"}
    for schema in TOOL_SCHEMAS:
        assert set(schema.keys()) >= {"name", "description", "input_schema"}
        assert schema["input_schema"]["type"] == "object"
        assert "properties" in schema["input_schema"]
