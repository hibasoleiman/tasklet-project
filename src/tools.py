"""Tool definitions and dispatch.

This module is the bridge between the LLM and the service layer. It owns:

  1. TOOL_SCHEMAS — the JSON sent to Anthropic on every API call. The
     schemas tell Claude what tools exist, what arguments they take, and
     (most importantly) WHEN to use each one. The descriptions here are
     among the most influential prompts in the whole system; tweak them
     to change agent behavior.

  2. dispatch() — given a parsed ToolUse from a Claude response, executes
     the right service function and packages the result as a ToolResult to
     feed back on the next agent loop iteration.

Security: dispatch() ALWAYS uses the user_id passed in by the caller (the
authenticated session) and NEVER reads user_id from the LLM's tool input.
A test in tests/test_tool_dispatch.py asserts this directly. If the LLM
tries to pass user_id, it is silently dropped (Pydantic ignores extra
fields by default in v2, and dispatch() never references the raw input
for user_id either way).
"""

import json
import sqlite3

from pydantic import ValidationError

from src.models import (
    QueryFilters,
    TicketCreate,
    ToolResult,
    ToolUse,
)
from src.query_service import get_ticket_by_id, list_tickets
from src.ticket_service import create_ticket

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "create_ticket",
        "description": (
            "Create a new support ticket on behalf of the current user. "
            "Use this when the user wants to file a new issue, request, or question. "
            "Before calling this tool, make sure you have collected all four required "
            "fields: a clear short title, a detailed description, the right category, "
            "and an appropriate priority. If anything is missing or ambiguous, ask the "
            "user a clarifying question instead of calling the tool."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short, specific title for the ticket. Max 200 characters.",
                },
                "description": {
                    "type": "string",
                    "description": "Full description of the issue, request, or question.",
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "bug_report",
                        "feature_request",
                        "billing",
                        "integration_issue",
                        "how_to_question",
                    ],
                    "description": (
                        "Category of the ticket. Pick the closest match: "
                        "bug_report for things that are broken; "
                        "feature_request for new capabilities; "
                        "billing for invoices, plans, or payment; "
                        "integration_issue for problems with external systems "
                        "(GitHub, Slack, Jira, etc.); "
                        "how_to_question for usage questions where nothing is broken."
                    ),
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": (
                        "Priority. Pick urgent for outages or anything blocking the user "
                        "right now; high for serious problems with workarounds; "
                        "medium for normal day-to-day issues; low for nice-to-haves "
                        "and minor questions."
                    ),
                },
            },
            "required": ["title", "description", "category", "priority"],
        },
    },
    {
        "name": "list_tickets",
        "description": (
            "Return tickets belonging to the current user, optionally filtered. "
            "Use this for 'show me my tickets', 'what's open', 'any urgent bugs', "
            "and similar lookups. All filters are optional — omit a filter to leave "
            "that dimension unconstrained. Results are automatically scoped to the "
            "current user; you do not need to (and cannot) specify a user."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": [
                        "open",
                        "in_progress",
                        "waiting_on_customer",
                        "resolved",
                        "closed",
                    ],
                    "description": "Restrict to tickets with this status.",
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "bug_report",
                        "feature_request",
                        "billing",
                        "integration_issue",
                        "how_to_question",
                    ],
                    "description": "Restrict to tickets in this category.",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "Restrict to tickets at this priority.",
                },
                "created_after": {
                    "type": "string",
                    "format": "date-time",
                    "description": (
                        "ISO 8601 datetime. Only return tickets created at or after "
                        "this moment. Example: '2026-04-01T00:00:00'."
                    ),
                },
                "created_before": {
                    "type": "string",
                    "format": "date-time",
                    "description": (
                        "ISO 8601 datetime. Only return tickets created at or before "
                        "this moment. Example: '2026-04-25T23:59:59'."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 500,
                    "description": (
                        "Optional cap on number of results, useful for "
                        "'my 5 most recent'. Omit to return all matches."
                    ),
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_ticket_by_id",
        "description": (
            "Look up one specific ticket by its numeric id. "
            "Returns the full ticket if it exists and is owned by the current user, "
            "otherwise returns a 'not found' response. Use this when the user "
            "references a specific ticket id (e.g., 'what's the status of ticket 42')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "integer",
                    "description": "The numeric id of the ticket to look up.",
                },
            },
            "required": ["ticket_id"],
        },
    },
]


def dispatch(
    conn: sqlite3.Connection, user_id: int, tool_use: ToolUse
) -> ToolResult:
    """Execute the named tool and return a ToolResult to feed back to the LLM.

    The user_id parameter is the authenticated user's id. This function NEVER
    reads user_id from tool_use.input — even if the LLM tries to pass one,
    it is ignored. Tests prove this.
    """
    name = tool_use.name
    raw_input = tool_use.input

    try:
        if name == "create_ticket":
            ticket_create = TicketCreate(**raw_input)
            ticket = create_ticket(conn, user_id, ticket_create)
            return _ok(tool_use.id, ticket.model_dump(mode="json"))

        if name == "list_tickets":
            filters = QueryFilters(**raw_input)
            tickets = list_tickets(conn, user_id, filters)
            return _ok(
                tool_use.id,
                {
                    "count": len(tickets),
                    "tickets": [t.model_dump(mode="json") for t in tickets],
                },
            )

        if name == "get_ticket_by_id":
            ticket_id = raw_input.get("ticket_id")
            if not isinstance(ticket_id, int) or isinstance(ticket_id, bool):
                return _err(
                    tool_use.id,
                    "ticket_id is required and must be an integer.",
                )
            ticket = get_ticket_by_id(conn, user_id, ticket_id)
            if ticket is None:
                return _ok(
                    tool_use.id,
                    {"found": False, "ticket_id": ticket_id},
                )
            return _ok(
                tool_use.id,
                {"found": True, "ticket": ticket.model_dump(mode="json")},
            )

        return _err(tool_use.id, f"Unknown tool: {name!r}")

    except ValidationError as e:
        # Hand the validation error back as a tool_result. On the next loop
        # iteration Claude reads this and (usually) corrects its input.
        return _err(tool_use.id, f"Input validation failed: {e}")
    except sqlite3.Error as e:
        # Don't leak SQL internals to the LLM. In production you would also
        # emit structured telemetry from here so an operator can investigate.
        return _err(tool_use.id, f"Database error: {type(e).__name__}")


def _ok(tool_use_id: str, payload: object) -> ToolResult:
    return ToolResult(
        tool_use_id=tool_use_id,
        content=json.dumps(payload),
        is_error=False,
    )


def _err(tool_use_id: str, message: str) -> ToolResult:
    return ToolResult(
        tool_use_id=tool_use_id,
        content=message,
        is_error=True,
    )
