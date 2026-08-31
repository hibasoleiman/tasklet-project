"""Regression guard for the refusal instructions in the system prompt.

This does NOT test the model's actual behavior — that requires a live API
call and is verified interactively (see "Refusal red-teaming" in
README.md). All this checks is that nobody quietly waters down or deletes
the refusal language in prompts.py in a future edit. If this test fails,
either the edit was accidental (restore the language) or intentional (update
this test AND re-run the red-team walkthrough in README.md before trusting
the new prompt).
"""

from src.prompts import SYSTEM_PROMPT


def test_system_prompt_states_the_three_tools_are_the_only_capability():
    assert "ONLY create new tickets and look up existing ones" in SYSTEM_PROMPT


def test_system_prompt_refuses_ticket_mutation():
    assert "cannot modify, delete, reassign, close, or change the status" in SYSTEM_PROMPT


def test_system_prompt_forbids_claiming_unavailable_actions():
    # The specific failure mode red-teamed in README.md #1: the agent must
    # never imply it took an action (e.g. "I'll forward this") that it
    # cannot actually perform.
    assert "would be misleading" in SYSTEM_PROMPT


def test_system_prompt_states_user_isolation():
    assert "do not see and cannot access other users' tickets" in SYSTEM_PROMPT
