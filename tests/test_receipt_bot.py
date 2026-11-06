"""Project 1: tests for the ReceiptBot profile, history, commands, and invalid input.

All tests run offline (FakeLLM), no API key needed:  python -m pytest tests/test_receipt_bot.py
"""

from ribot.receipt_bot import (
    EMPTY_INPUT_MSG,
    MAX_INPUT_CHARS,
    handle_input,
    new_bot,
)
from ribot.receipt_profile import RECEIPT_PROFILE, build_profile_prompt


# --- Assistant profile -------------------------------------------------------

def test_profile_has_all_required_parts():
    for key in ("role", "tone", "rules", "answer_requirements", "boundaries"):
        assert RECEIPT_PROFILE[key], f"profile is missing {key}"


def test_profile_prompt_includes_each_section():
    prompt = build_profile_prompt()
    assert prompt.startswith("You are ReceiptBot")
    for heading in ("Tone:", "Operating rules:", "Answer requirements:", "Boundaries:"):
        assert heading in prompt


def test_bot_uses_receipt_profile_as_system_prompt():
    bot = new_bot()
    assert bot.history[0] == {"role": "system", "content": build_profile_prompt()}


# --- Conversation history ----------------------------------------------------

def test_question_and_answer_are_added_to_history():
    bot = new_bot()
    handle_input(bot, "How much did the milk cost?")
    assert bot.history[-2] == {"role": "user", "content": "How much did the milk cost?"}
    assert bot.history[-1]["role"] == "assistant"


def test_history_grows_across_turns():
    bot = new_bot()
    handle_input(bot, "What did I buy at Walmart?")
    handle_input(bot, "How much was that?")
    assert len(bot.history) == 1 + 4  # system + two (user, assistant) pairs


def test_history_lets_bot_recall_earlier_turns():
    # FakeLLM's memory demo: it can only recall the name if the earlier turn is in history.
    bot = new_bot()
    handle_input(bot, "My name is Mike.")
    reply, _ = handle_input(bot, "What's my name?")
    assert "Mike" in reply


# --- Commands ----------------------------------------------------------------

def test_exit_stops_the_loop():
    _, keep_running = handle_input(new_bot(), "/exit")
    assert keep_running is False


def test_exit_is_case_insensitive():
    _, keep_running = handle_input(new_bot(), "  /EXIT ")
    assert keep_running is False


def test_help_lists_every_command():
    text, keep_running = handle_input(new_bot(), "/help")
    assert keep_running
    for cmd in ("/help", "/history", "/reset", "/exit"):
        assert cmd in text


def test_history_command_shows_turns_without_changing_history():
    bot = new_bot()
    handle_input(bot, "What did I buy at Walmart?")
    before = list(bot.history)
    text, _ = handle_input(bot, "/history")
    assert "[user] What did I buy at Walmart?" in text
    assert bot.history == before


def test_reset_clears_everything_but_the_profile():
    bot = new_bot()
    handle_input(bot, "What did I buy at Walmart?")
    handle_input(bot, "/reset")
    assert bot.history == [{"role": "system", "content": build_profile_prompt()}]


def test_commands_are_not_added_to_history():
    bot = new_bot()
    for cmd in ("/help", "/history"):
        handle_input(bot, cmd)
    assert len(bot.history) == 1


# --- Invalid input -----------------------------------------------------------

def test_empty_input_gets_a_message_and_is_not_saved():
    bot = new_bot()
    for raw in ("", "   ", "\t\n"):
        text, keep_running = handle_input(bot, raw)
        assert text == EMPTY_INPUT_MSG
        assert keep_running
    assert len(bot.history) == 1


def test_too_long_input_is_rejected():
    bot = new_bot()
    text, keep_running = handle_input(bot, "x" * (MAX_INPUT_CHARS + 1))
    assert "too long" in text
    assert keep_running
    assert len(bot.history) == 1


def test_unknown_command_is_rejected():
    bot = new_bot()
    text, keep_running = handle_input(bot, "/delete")
    assert "Unknown command '/delete'" in text
    assert keep_running
    assert len(bot.history) == 1
