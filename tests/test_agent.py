"""Tests for the agent loop.

We mock the Anthropic client so these run offline. The mock is intentionally
tiny and ducktyped — students should be able to read it and understand
exactly what the real client returns. Two tests:

  * happy path: text-only response → agent returns that text, no tools called.
  * cap path: client always asks for a tool → loop bails at MAX_TOOL_CALLS.

If you want to test agent routing live (does Claude pick the right tool for
a given user prompt?), do that interactively against the real API — see the
demo walkthrough in the README.
"""

from src import agent
from src.conversation import Conversation


class _Block:
    """Ducktyped stand-in for an Anthropic content block."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _Response:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason


class _Messages:
    def __init__(self, response_factory):
        self._factory = response_factory

    def create(self, **kwargs):
        return self._factory(kwargs)


class FakeClient:
    """Returns whatever a caller supplies, one response at a time."""

    def __init__(self, responses):
        self._iter = iter(responses)
        self.messages = _Messages(lambda kw: next(self._iter))


def test_run_turn_returns_text_when_no_tool_call(conn, seed_users):
    fake = FakeClient(
        responses=[
            _Response(
                content=[_Block(type="text", text="Hi there. How can I help?")],
                stop_reason="end_turn",
            )
        ]
    )
    conv = Conversation.load_or_create(conn, user_id=1)
    result = agent.run_turn(
        client=fake, conn=conn, conversation=conv, user_input="hello"
    )
    assert result.final_text == "Hi there. How can I help?"
    assert result.tool_call_count == 0
    # User message + assistant message = 2 entries
    assert len(conv.messages) == 2


def test_run_turn_caps_tool_calls(conn, seed_tickets):
    """Claude that keeps requesting tool calls is stopped at MAX_TOOL_CALLS."""

    def always_tool_use(_kwargs):
        return _Response(
            content=[
                _Block(
                    type="tool_use",
                    id="t",
                    name="list_tickets",
                    input={},
                )
            ],
            stop_reason="tool_use",
        )

    fake = FakeClient.__new__(FakeClient)
    fake.messages = _Messages(always_tool_use)

    conv = Conversation.load_or_create(conn, user_id=1)
    result = agent.run_turn(
        client=fake, conn=conn, conversation=conv, user_input="loop forever"
    )
    assert result.tool_call_count == agent.MAX_TOOL_CALLS
    assert "maximum" in result.final_text.lower()


def test_run_turn_marks_system_prompt_as_cache_breakpoint(conn, seed_users):
    """Prompt caching: the system block should carry an ephemeral
    cache_control marker. Anthropic checks a request in the order
    tools -> system -> messages, so this one breakpoint is enough to cache
    both the (also-static) tool schemas and the system prompt together."""
    captured = {}

    def capture(kwargs):
        captured.update(kwargs)
        return _Response(
            content=[_Block(type="text", text="hi")],
            stop_reason="end_turn",
        )

    fake = FakeClient.__new__(FakeClient)
    fake.messages = _Messages(capture)

    conv = Conversation.load_or_create(conn, user_id=1)
    agent.run_turn(client=fake, conn=conn, conversation=conv, user_input="hello")

    assert captured["system"] == [
        {
            "type": "text",
            "text": agent.SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }
    ]
    assert captured["tools"] == agent.TOOL_SCHEMAS


def test_run_turn_executes_one_tool_then_finishes(conn, seed_tickets):
    """Claude calls list_tickets, then on the next turn returns text. Verify
    the tool actually runs and the text is the final result."""
    responses = iter(
        [
            _Response(
                content=[
                    _Block(
                        type="tool_use",
                        id="t1",
                        name="list_tickets",
                        input={"status": "open"},
                    )
                ],
                stop_reason="tool_use",
            ),
            _Response(
                content=[_Block(type="text", text="You have 1 open ticket: Alpha bug.")],
                stop_reason="end_turn",
            ),
        ]
    )
    fake = FakeClient.__new__(FakeClient)
    fake.messages = _Messages(lambda kw: next(responses))

    conv = Conversation.load_or_create(conn, user_id=1)
    result = agent.run_turn(
        client=fake, conn=conn, conversation=conv, user_input="what's open?"
    )
    assert result.tool_call_count == 1
    assert result.final_text == "You have 1 open ticket: Alpha bug."
    # user + assistant(tool_use) + tool(result) + assistant(text) = 4 messages
    assert len(conv.messages) == 4
    assert conv.messages[2].role == "tool"
    assert conv.messages[2].tool_result.is_error is False
