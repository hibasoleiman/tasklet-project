"""CLI for the Tasklet support agent.

Usage:
    python3 main.py --user-id 1              # chat as user 1
    python3 main.py --user-id 1 --new        # start a fresh conversation
    python3 main.py --user-id 1 --verbose    # print every tool call
    python3 main.py --init-db                # wipe and reseed the database
    python3 main.py --list-users             # show available users
"""

import argparse
import os
import sys

from anthropic import Anthropic
from dotenv import load_dotenv

from src.agent import run_turn
from src.conversation import Conversation
from src.db import get_connection, init_db
from src.models import ToolResult, ToolUse


def main() -> None:
    parser = argparse.ArgumentParser(description="Tasklet Support Agent CLI")
    parser.add_argument("--init-db", action="store_true", help="Wipe and reseed the database.")
    parser.add_argument("--list-users", action="store_true", help="List available users.")
    parser.add_argument("--user-id", type=int, help="User to chat as.")
    parser.add_argument("--new", action="store_true", help="Start a fresh conversation.")
    parser.add_argument("--verbose", action="store_true", help="Print every tool call and its result.")
    args = parser.parse_args()

    if args.init_db:
        init_db()
        print("Database initialized.")
        return

    if args.list_users:
        conn = get_connection()
        rows = conn.execute("SELECT id, email, name FROM users ORDER BY id").fetchall()
        if not rows:
            print("No users found. Run `python3 main.py --init-db` first.")
            sys.exit(1)
        for r in rows:
            print(f"  {r['id']:>3}  {r['name']:<20}  {r['email']}")
        conn.close()
        return

    if args.user_id is None:
        parser.print_help()
        sys.exit(1)

    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set. Add it to .env or export it.", file=sys.stderr)
        sys.exit(2)

    conn = get_connection()
    user_row = conn.execute(
        "SELECT id, name FROM users WHERE id = ?", (args.user_id,)
    ).fetchone()
    if user_row is None:
        print(f"No user with id {args.user_id}. Run `python3 main.py --list-users` to see options.", file=sys.stderr)
        sys.exit(2)

    conversation = (
        Conversation.new(conn, args.user_id)
        if args.new
        else Conversation.load_or_create(conn, args.user_id)
    )

    client = Anthropic(api_key=api_key)

    print(f"Chatting as {user_row['name']} (user id {args.user_id}).")
    if conversation.messages and not args.new:
        print(
            f"Resumed conversation with {len(conversation.messages)} prior messages. "
            "Use --new to start fresh."
        )
    print("Type 'exit' or press Ctrl-D to leave.\n")

    def on_tool_call(tu: ToolUse, tr: ToolResult) -> None:
        prefix = "[tool error]" if tr.is_error else "[tool]"
        snippet = tr.content if len(tr.content) <= 200 else tr.content[:200] + "..."
        print(f"  {prefix} {tu.name}({tu.input}) -> {snippet}")

    while True:
        try:
            user_input = input("you: ")
        except EOFError:
            print("\nGoodbye.")
            break

        if user_input.strip().lower() in ("exit", "quit"):
            print("Goodbye.")
            break
        if not user_input.strip():
            continue

        try:
            result = run_turn(
                client=client,
                conn=conn,
                conversation=conversation,
                user_input=user_input,
                on_tool_call=on_tool_call if args.verbose else None,
            )
            print(f"agent: {result.final_text}\n")
        except Exception as e:  # noqa: BLE001
            print(f"[error] {type(e).__name__}: {e}", file=sys.stderr)

    conn.close()


if __name__ == "__main__":
    main()
