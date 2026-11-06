"""Tests for the ReceiptBot profile, history, commands, invalid input, and save/load.

All tests run offline (FakeLLM), no API key needed:  python -m pytest project2/tests
"""

import json

import pytest

from project2.receipt_bot import (
    COMMANDS,
    EMPTY_INPUT_MSG,
    MAX_INPUT_CHARS,
    InvalidInputError,
    build_system_prompt,
    handle_input,
    new_session,
    parse_command,
    validate_input,
)
from ribot.receipt_profile import RECEIPT_PROFILE, build_profile_prompt
from project2.receipts import load_receipts


@pytest.fixture
def session(tmp_path):
    """A fresh session that saves conversations into a temporary folder."""
    return new_session(conversations_dir=tmp_path)


def system_message(session):
    return {"role": "system", "content": build_system_prompt(session.receipts)}


# --- Synthetic receipt data --------------------------------------------------

def test_three_receipts_with_fifteen_items():
    receipts = load_receipts()
    assert len(receipts) == 3
    assert sum(len(r["items"]) for r in receipts) == 15
    assert all(len(r["items"]) <= 5 for r in receipts)


def test_receipt_math_adds_up():
    for r in load_receipts():
        assert round(sum(i["price"] for i in r["items"]), 2) == r["subtotal"], r["id"]
        assert round(r["subtotal"] + r["tax"], 2) == r["total"], r["id"]


def test_system_prompt_contains_every_item(session):
    prompt = session.bot.history[0]["content"]
    for r in session.receipts:
        for item in r["items"]:
            assert item["name"] in prompt


def test_session_uses_receipts_passed_in(tmp_path):
    # Receipts are injected, not re-read from disk, so tests can use their own data.
    fake = [dict(load_receipts()[0], id="T1", store="TestMart")]
    s = new_session(receipts=fake, conversations_dir=tmp_path)
    assert "TestMart" in s.bot.history[0]["content"]
    assert "TestMart" in handle_input(s, "/receipts").text


# --- Assistant profile -------------------------------------------------------

def test_profile_has_all_required_parts():
    for key in ("role", "tone", "rules", "answer_requirements", "boundaries"):
        assert RECEIPT_PROFILE[key], f"profile is missing {key}"


def test_profile_prompt_includes_each_section():
    prompt = build_profile_prompt()
    assert prompt.startswith("You are ReceiptBot")
    for heading in ("Tone:", "Operating rules:", "Answer requirements:", "Boundaries:"):
        assert heading in prompt


def test_session_starts_with_profile_as_system_message(session):
    assert session.bot.history == [system_message(session)]
    assert session.bot.history[0]["content"].startswith(build_profile_prompt())


# --- Small functions: validate_input and parse_command ------------------------

@pytest.mark.parametrize("raw", ["", "   ", "\t\n"])
def test_validate_input_rejects_empty(raw):
    with pytest.raises(InvalidInputError, match="Please type a question"):
        validate_input(raw)


def test_validate_input_rejects_too_long():
    with pytest.raises(InvalidInputError, match="too long"):
        validate_input("x" * (MAX_INPUT_CHARS + 1))


def test_validate_input_strips_whitespace():
    assert validate_input("  How much was milk?  ") == "How much was milk?"


def test_parse_command_splits_name_and_argument():
    assert parse_command("/SAVE october") == ("/save", "october")
    assert parse_command("/help") == ("/help", "")


# --- Conversation history ----------------------------------------------------

def test_question_and_answer_are_added_to_history(session):
    handle_input(session, "How much did the milk cost?")
    assert session.bot.history[-2] == {"role": "user", "content": "How much did the milk cost?"}
    assert session.bot.history[-1]["role"] == "assistant"


def test_history_grows_across_turns(session):
    handle_input(session, "What did I buy at Walmart?")
    handle_input(session, "How much was that?")
    assert len(session.bot.history) == 1 + 4  # system + two (user, assistant) pairs


def test_history_lets_bot_recall_earlier_turns(session):
    # FakeLLM's memory demo: it can only recall the name if the earlier turn is in history.
    handle_input(session, "My name is Mike.")
    reply = handle_input(session, "What's my name?")
    assert "Mike" in reply.text


# --- Commands ----------------------------------------------------------------

def test_exit_stops_the_loop(session):
    assert handle_input(session, "/exit").keep_running is False


def test_exit_is_case_insensitive(session):
    assert handle_input(session, "  /EXIT ").keep_running is False


def test_help_lists_every_registered_command(session):
    text = handle_input(session, "/help").text
    for name in COMMANDS:
        assert name in text


def test_history_command_shows_turns_without_changing_history(session):
    handle_input(session, "What did I buy at Walmart?")
    before = list(session.bot.history)
    text = handle_input(session, "/history").text
    assert "[user] What did I buy at Walmart?" in text
    assert session.bot.history == before


def test_reset_clears_everything_but_the_profile(session):
    handle_input(session, "What did I buy at Walmart?")
    handle_input(session, "/reset")
    assert session.bot.history == [system_message(session)]


def test_commands_are_not_added_to_history(session):
    for cmd in ("/help", "/history", "/receipts"):
        handle_input(session, cmd)
    assert len(session.bot.history) == 1


# --- Invalid input -----------------------------------------------------------

def test_empty_input_gets_a_message_and_is_not_saved(session):
    for raw in ("", "   ", "\t\n"):
        reply = handle_input(session, raw)
        assert reply.text == EMPTY_INPUT_MSG
        assert reply.keep_running
    assert len(session.bot.history) == 1


def test_too_long_input_is_rejected(session):
    reply = handle_input(session, "x" * (MAX_INPUT_CHARS + 1))
    assert "too long" in reply.text
    assert reply.keep_running
    assert len(session.bot.history) == 1


def test_unknown_command_is_rejected(session):
    reply = handle_input(session, "/delete")
    assert "Unknown command '/delete'" in reply.text
    assert reply.keep_running
    assert len(session.bot.history) == 1


# --- /save and /load ---------------------------------------------------------

def test_save_then_load_restores_the_conversation(session, tmp_path):
    handle_input(session, "What did I buy at Walmart?")
    handle_input(session, "How much was that?")
    saved_history = list(session.bot.history)

    assert "Saved 4 message(s)" in handle_input(session, "/save october").text
    assert (tmp_path / "october.json").exists()

    handle_input(session, "/reset")
    assert len(session.bot.history) == 1

    assert "Loaded 4 message(s)" in handle_input(session, "/load october").text
    assert session.bot.history == saved_history


def test_memory_works_after_loading_into_a_new_session(tmp_path):
    first = new_session(conversations_dir=tmp_path)
    handle_input(first, "My name is Mike.")
    handle_input(first, "/save")

    second = new_session(conversations_dir=tmp_path)  # like restarting the program
    handle_input(second, "/load")
    assert "Mike" in handle_input(second, "What's my name?").text


def test_save_rejects_unsafe_name(session, tmp_path):
    reply = handle_input(session, "/save ../outside")
    assert reply.text.startswith("Not saved: Invalid name")
    assert list(tmp_path.iterdir()) == []


def test_load_missing_file_keeps_current_conversation(session):
    handle_input(session, "What did I buy at Walmart?")
    before = list(session.bot.history)
    reply = handle_input(session, "/load nothing_here")
    assert reply.text.startswith("Not loaded: No saved conversation")
    assert session.bot.history == before


def test_load_corrupted_file_keeps_current_conversation(session, tmp_path):
    (tmp_path / "broken.json").write_text('{"format_version": 1, "messages": [', encoding="utf-8")
    handle_input(session, "What did I buy at Walmart?")
    before = list(session.bot.history)
    reply = handle_input(session, "/load broken")
    assert "not valid JSON" in reply.text
    assert session.bot.history == before


def test_saved_file_does_not_contain_system_prompt(session, tmp_path):
    handle_input(session, "How much did the milk cost?")
    handle_input(session, "/save check")
    data = json.loads((tmp_path / "check.json").read_text(encoding="utf-8"))
    assert [m["role"] for m in data["messages"]] == ["user", "assistant"]
    assert "Receipts (the only data" not in json.dumps(data)
