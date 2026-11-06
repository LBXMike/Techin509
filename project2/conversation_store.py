"""Save a conversation to JSON and read it back.

Contract:
- save_conversation(history, path) writes the user/assistant turns and returns the path.
  The system message (profile + receipts) is NOT saved: it is rebuilt from the current
  profile and receipts when the conversation is loaded.
- load_conversation(path) returns the list of turns, or raises ConversationFileError
  if the file is missing, is not valid JSON, or does not match the expected format.
- Neither function talks to the model or prints anything.

File format (format_version 1):
    {
      "format_version": 1,
      "saved_at": "2026-11-05T14:03:00",
      "messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    }
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

FORMAT_VERSION = 1
SAVED_ROLES = ("user", "assistant")
CONVERSATIONS_DIR = Path(__file__).resolve().parent / "conversations"  # project2/conversations/

# Letters, digits, dash, underscore only: keeps /save names from escaping the folder.
_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")

Message = dict[str, str]


class ConversationFileError(ValueError):
    """A conversation file is missing, unreadable, or not in the expected format."""


def conversation_path(name: str, folder: Path = CONVERSATIONS_DIR) -> Path:
    """Turn a short name like 'october' into conversations/october.json.

    Raises ConversationFileError for names with spaces, slashes, dots, etc.
    """
    if not _NAME_RE.match(name):
        raise ConversationFileError(
            f"Invalid name {name!r}. Use 1-40 letters, numbers, '-' or '_' (no spaces or dots)."
        )
    return Path(folder) / f"{name}.json"


def turns_only(history: list[Message]) -> list[Message]:
    """Drop the system message, keeping just the user/assistant turns."""
    return [dict(m) for m in history if m["role"] in SAVED_ROLES]


def validate_messages(messages: object) -> list[Message]:
    """Check a loaded list of messages; raise ConversationFileError on the first problem."""
    if not isinstance(messages, list):
        raise ConversationFileError("'messages' must be a list.")
    for n, msg in enumerate(messages, start=1):
        if not isinstance(msg, dict) or set(msg) != {"role", "content"}:
            raise ConversationFileError(
                f"Message {n} must have exactly 'role' and 'content' fields."
            )
        if msg["role"] not in SAVED_ROLES:
            raise ConversationFileError(
                f"Message {n} has role {msg['role']!r}; expected 'user' or 'assistant'."
            )
        if not isinstance(msg["content"], str):
            raise ConversationFileError(f"Message {n} content must be text.")
    return messages


def save_conversation(history: list[Message], path: Path) -> Path:
    """Write the conversation turns to `path` as JSON. Creates the folder if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format_version": FORMAT_VERSION,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "messages": turns_only(history),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


def load_conversation(path: Path) -> list[Message]:
    """Read a saved conversation and return its user/assistant turns."""
    path = Path(path)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise ConversationFileError(f"No saved conversation at {path.name}.") from None
    except json.JSONDecodeError as e:
        raise ConversationFileError(
            f"{path.name} is not valid JSON (line {e.lineno}, column {e.colno})."
        ) from None
    if not isinstance(data, dict):
        raise ConversationFileError(f"{path.name} should contain a JSON object.")
    if data.get("format_version") != FORMAT_VERSION:
        raise ConversationFileError(
            f"{path.name} has format_version {data.get('format_version')!r}; "
            f"this version of ReceiptBot reads version {FORMAT_VERSION}."
        )
    return validate_messages(data.get("messages"))
