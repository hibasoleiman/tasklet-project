"""Pydantic models for the Tasklet support agent.

Every input the LLM produces (tool inputs) and every record we store
(users, tickets, conversation messages) is one of these models.

These models are the contract between three layers:
  1. The LLM — its tool inputs must validate as TicketCreate or QueryFilters.
  2. The service layer — it accepts and returns these models.
  3. The database — rows materialize back into Ticket / User / AgentMessage.

If the LLM emits a bad enum or a malformed date, Pydantic raises a
ValidationError and the agent loop turns that error into a tool_result so
Claude can self-correct on the next iteration.
"""

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Category(str, Enum):
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    BILLING = "billing"
    INTEGRATION_ISSUE = "integration_issue"
    HOW_TO_QUESTION = "how_to_question"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Status(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_ON_CUSTOMER = "waiting_on_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class User(BaseModel):
    id: int
    email: str
    name: str


class TicketCreate(BaseModel):
    """Fields the LLM must collect from the user before calling create_ticket."""

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    category: Category
    priority: Priority


class Ticket(TicketCreate):
    """A persisted ticket. Includes server-assigned fields the LLM never sets."""

    id: int
    user_id: int
    status: Status
    created_at: datetime
    updated_at: datetime


class QueryFilters(BaseModel):
    """Tool input for list_tickets. All fields optional — the LLM picks which to set.

    There is no default cap on results: the user wants the agent to return
    every matching ticket so summaries are accurate. The optional `limit` is
    available if the LLM wants to ask for "my 5 most recent" specifically.
    """

    status: Optional[Status] = None
    category: Optional[Category] = None
    priority: Optional[Priority] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: Optional[int] = Field(default=None, ge=1, le=500)


class ToolUse(BaseModel):
    """A single tool invocation emitted by the assistant."""

    id: str
    name: str
    input: dict


class ToolResult(BaseModel):
    """The result of executing a tool, fed back to the assistant on the next turn."""

    tool_use_id: str
    content: str
    is_error: bool = False


class AgentMessage(BaseModel):
    """One entry in the conversation history.

    role='user'      — a user message (content set, no tool fields).
    role='assistant' — a Claude response (content optional, tool_calls may have one entry).
    role='tool'      — a tool execution result (tool_result set).

    The agent loop is sequential: the system prompt instructs Claude to issue
    at most one tool call per turn. Storing one tool call per assistant
    message and one result per tool message keeps the log easy to read.

    Note: the actual stateful Conversation object lives in src/conversation.py
    (not here). It owns persistence and exposes append/reset/load methods.
    """

    role: Literal["user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: list[ToolUse] = Field(default_factory=list)
    tool_result: Optional[ToolResult] = None
