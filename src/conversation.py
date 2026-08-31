"""Conversation state — the multi-turn message history for one user session.

Conversation owns three things:

  1. An in-memory list of AgentMessage (the working state).
  2. Persistence to the conversations/messages tables in SQLite (so a
     refresh or a re-launched CLI resumes where it left off).
  3. Conversion to the shape the Anthropic API expects (collapsing our
     three internal roles into Anthropic's two: 'user' and 'assistant').

Two ways to start a Conversation:

  Conversation.load_or_create(conn, user_id) — resume the most recent
    conversation for this user, or create a new row if there is none.

  Conversation.new(conn, user_id) — always start a fresh conversation,
    ignoring any existing one. Used by the CLI's --new flag and the
    Streamlit "Reset conversation" button (which actually wipes messages
    in place; see reset()).
"""

import sqlite3

from src.models import AgentMessage


class Conversation:
    def __init__(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        conversation_id: int,
        messages: list[AgentMessage],
    ) -> None:
        self.conn = conn
        self.user_id = user_id
        self.id = conversation_id
        self.messages = messages

    # ---------- factory methods ----------

    @classmethod
    def load_or_create(cls, conn: sqlite3.Connection, user_id: int) -> "Conversation":
        """Return the user's most recent conversation, or a new empty one."""
        row = conn.execute(
            "SELECT id FROM conversations WHERE user_id = ? "
            "ORDER BY updated_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        if row is not None:
            conv_id = row["id"]
            messages = cls._load_messages(conn, conv_id)
            return cls(conn, user_id, conv_id, messages)
        return cls.new(conn, user_id)

    @classmethod
    def new(cls, conn: sqlite3.Connection, user_id: int) -> "Conversation":
        """Always start a fresh conversation row, ignoring any existing one."""
        cur = conn.execute(
            "INSERT INTO conversations (user_id) VALUES (?)", (user_id,)
        )
        conn.commit()
        return cls(conn, user_id, cur.lastrowid, [])

    @staticmethod
    def _load_messages(conn: sqlite3.Connection, conv_id: int) -> list[AgentMessage]:
        rows = conn.execute(
            "SELECT content FROM messages WHERE conversation_id = ? ORDER BY id",
            (conv_id,),
        ).fetchall()
        return [AgentMessage.model_validate_json(row["content"]) for row in rows]

    # ---------- mutators ----------

    def append(self, message: AgentMessage) -> None:
        """Append in-memory and persist to SQLite in one shot."""
        self.messages.append(message)
        self.conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (self.id, message.role, message.model_dump_json()),
        )
        self.conn.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (self.id,),
        )
        self.conn.commit()

    def reset(self) -> None:
        """Delete every message in this conversation, keeping the conversation row."""
        self.conn.execute(
            "DELETE FROM messages WHERE conversation_id = ?", (self.id,)
        )
        self.conn.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (self.id,),
        )
        self.conn.commit()
        self.messages = []

    # ---------- API serialization ----------

    def to_anthropic_messages(self) -> list[dict]:
        """Convert our message log to the shape the Anthropic API expects.

        Anthropic uses two roles only: 'user' and 'assistant'. Tool results
        are sent as a 'user'-role message containing one or more tool_result
        content blocks. We flatten our internal 'tool' role into that shape
        here. This is the one place that crosses our model boundary into the
        Anthropic SDK's, and it is small on purpose.
        """
        result: list[dict] = []
        for msg in self.messages:
            if msg.role == "user":
                result.append({"role": "user", "content": msg.content or ""})
            elif msg.role == "tool":
                tr = msg.tool_result
                assert tr is not None, "tool message with no tool_result"
                result.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tr.tool_use_id,
                                "content": tr.content,
                                "is_error": tr.is_error,
                            }
                        ],
                    }
                )
            elif msg.role == "assistant":
                blocks: list[dict] = []
                if msg.content:
                    blocks.append({"type": "text", "text": msg.content})
                for tu in msg.tool_calls:
                    blocks.append(
                        {
                            "type": "tool_use",
                            "id": tu.id,
                            "name": tu.name,
                            "input": tu.input,
                        }
                    )
                result.append({"role": "assistant", "content": blocks})
        return result
