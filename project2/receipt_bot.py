"""ReceiptBot: the command loop.

Run it:  python -m project2.receipt_bot

How the pieces fit (each function has one job):

    main()                 read a line, print the reply, stop on /exit
      handle_input()       route one line of input
        validate_input()   empty / too long -> InvalidInputError
        parse_command()    "/save october" -> ("/save", "october")
        COMMANDS[...]      one table: name -> (description, handler)
        ask()              normal question -> model, history updated

Memory: `session.bot.history` is the single source of truth. It always starts with the
system message (profile + receipts) followed by user/assistant turns. Every model call
sends the whole list, so follow-up questions can refer to earlier ones. /save writes the
turns to JSON and /load puts them back behind a fresh system message.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, NamedTuple

# Reused from Project 1 without changes.
from ribot.chatbot import ChatBot
from ribot.receipt_profile import build_profile_prompt

# New in Project 2.
from .conversation_store import (
    CONVERSATIONS_DIR,
    ConversationFileError,
    conversation_path,
    load_conversation,
    save_conversation,
    turns_only,
)
from .receipts import ReceiptDataError, format_receipts, load_receipts, receipts_summary

MAX_INPUT_CHARS = 500
DEFAULT_SAVE_NAME = "latest"

EMPTY_INPUT_MSG = "Please type a question about your receipts (or /help for commands)."
TOO_LONG_MSG = "That message is too long ({n} characters). Please keep questions under {max} characters."
UNKNOWN_COMMAND_MSG = "Unknown command '{cmd}'. Type /help to see the commands."


# --- Data passed between functions ---------------------------------------------

class Reply(NamedTuple):
    """What handle_input returns: text to show, and whether the loop keeps going."""

    text: str
    keep_running: bool = True


@dataclass
class Session:
    """Everything one conversation needs. Built once by new_session()."""

    bot: ChatBot
    receipts: list[dict]
    conversations_dir: Path = field(default=CONVERSATIONS_DIR)
    # Steering: was the previous question on topic? Lets a follow-up like
    # "How much was that?" through. Blocked questions set it to False.
    last_was_receipt: bool = False


class InvalidInputError(ValueError):
    """The user's input can't be used (empty or too long). The message says why."""


# --- Building a session ----------------------------------------------------------

def build_system_prompt(receipts: list[dict]) -> str:
    """The ReceiptBot profile plus the receipts it answers from."""
    return build_profile_prompt(receipts_text=format_receipts(receipts))


def new_session(
    receipts: list[dict] | None = None, conversations_dir: Path = CONVERSATIONS_DIR
) -> Session:
    """Create a session. Loads receipts from disk unless they are passed in (tests do)."""
    if receipts is None:
        receipts = load_receipts()
    bot = ChatBot(system_prompt=build_system_prompt(receipts))
    return Session(bot=bot, receipts=receipts, conversations_dir=Path(conversations_dir))


def restore_turns(session: Session, turns: list[dict[str, str]]) -> None:
    """Replace the conversation with saved turns, keeping the current system message."""
    session.bot.history = session.bot.history[:1] + [dict(t) for t in turns]


# --- Input checks ------------------------------------------------------------------

def validate_input(raw: str) -> str:
    """Return the cleaned input, or raise InvalidInputError with a message for the user."""
    text = raw.strip()
    if not text:
        raise InvalidInputError(EMPTY_INPUT_MSG)
    if len(text) > MAX_INPUT_CHARS:
        raise InvalidInputError(TOO_LONG_MSG.format(n=len(text), max=MAX_INPUT_CHARS))
    return text


def parse_command(text: str) -> tuple[str, str]:
    """Split '/save october' into ('/save', 'october'). The name is lowercased."""
    name, _, arg = text.partition(" ")
    return name.lower(), arg.strip()


# --- Command handlers: each takes (session, arg) and returns a Reply ------------

def cmd_help(session: Session, arg: str) -> Reply:
    lines = [f"  {name:<10} {cmd.description}" for name, cmd in COMMANDS.items()]
    return Reply("Commands:\n" + "\n".join(lines))


def cmd_receipts(session: Session, arg: str) -> Reply:
    return Reply("Receipts on file:\n" + receipts_summary(session.receipts))


def cmd_history(session: Session, arg: str) -> Reply:
    history = session.bot.history
    lines = []
    for i, msg in enumerate(history):
        content = msg["content"]
        if msg["role"] == "system":
            content = content.splitlines()[0] + " ... (profile)"
        lines.append(f"  {i}. [{msg['role']}] {content}")
    lines.append(f"  ({len(turns_only(history)) // 2} question(s) so far)")
    return Reply("\n".join(lines))


def cmd_reset(session: Session, arg: str) -> Reply:
    session.bot.reset()
    session.last_was_receipt = False  # nothing to follow up on after a reset
    return Reply("History cleared. Starting a new conversation.")


def cmd_save(session: Session, arg: str) -> Reply:
    try:
        path = conversation_path(arg or DEFAULT_SAVE_NAME, session.conversations_dir)
        save_conversation(session.bot.history, path)
    except ConversationFileError as e:
        return Reply(f"Not saved: {e}")
    except OSError as e:
        return Reply(f"Not saved: could not write the file ({e.strerror}).")
    turns = len(turns_only(session.bot.history))
    return Reply(f"Saved {turns} message(s) to conversations/{path.name}.")


def cmd_load(session: Session, arg: str) -> Reply:
    try:
        path = conversation_path(arg or DEFAULT_SAVE_NAME, session.conversations_dir)
        turns = load_conversation(path)
    except ConversationFileError as e:
        # The current conversation is left untouched when a load fails.
        return Reply(f"Not loaded: {e}")
    restore_turns(session, turns)
    return Reply(f"Loaded {len(turns)} message(s) from conversations/{path.name}.")


def cmd_exit(session: Session, arg: str) -> Reply:
    return Reply("Goodbye!", keep_running=False)


class Command(NamedTuple):
    description: str
    handler: Callable[[Session, str], Reply]


# The one place commands are defined. /help is generated from this table,
# so adding a command is a single edit.
COMMANDS: dict[str, Command] = {
    "/help": Command("show this list of commands", cmd_help),
    "/receipts": Command("list the receipts ReceiptBot can see", cmd_receipts),
    "/history": Command("print the conversation history the model sees", cmd_history),
    "/save": Command("save the conversation: /save [name] (default: latest)", cmd_save),
    "/load": Command("load a saved conversation: /load [name] (default: latest)", cmd_load),
    "/reset": Command("clear the history and start a new conversation", cmd_reset),
    "/exit": Command("quit ReceiptBot", cmd_exit),
}


# --- Steering: keep questions about the receipts (Week 7 studio, issue #1) -------

# General receipt words from the issue, plus their common forms.
GENERAL_RECEIPT_WORDS = frozenset({
    "total", "totals", "subtotal", "price", "prices", "cost", "costs", "spend", "spent",
    "buy", "bought", "receipt", "receipts", "tax", "paid", "purchase", "purchases",
    # Added after review: real receipt questions that were being blocked.
    "pay", "item", "items", "store", "stores", "shop", "shopped",
})

# Words that refer back to the previous question ("How much was that?").
FOLLOW_UP_CUES = frozenset({"that", "it", "this", "those", "these", "them", "one"})

CARD_WORDS = frozenset({"card", "cards"})
CARD_INFO_MSG = "I don't store card information for safety reasons."


def _words(text: str) -> set[str]:
    """Lowercased whole words. Dates like 2026-10-01 stay one word."""
    return set(re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)*", text.lower()))


def _item_noun(item: dict) -> str:
    """The distinctive part of an item name: 'Eggs, large, 1 dozen' -> 'Eggs'."""
    return item["name"].split(",")[0].strip()


def receipt_keywords(receipts: list[dict]) -> set[str]:
    """Words that mark a question as receipt-related, built from the receipts data.

    Store names, dates, and each item's noun (the part before the first comma), plus
    GENERAL_RECEIPT_WORDS. Descriptors after the comma ('white', 'large') are left out,
    so they can't make an unrelated question look on topic.
    """
    keywords = set(GENERAL_RECEIPT_WORDS)
    for receipt in receipts:
        keywords |= _words(receipt["store"])
        keywords.add(receipt["date"])
        for item in receipt["items"]:
            keywords |= _words(_item_noun(item))
    return keywords


def is_receipt_question(text: str, receipts: list[dict]) -> bool:
    """True if the question shares a whole word with receipt_keywords(receipts)."""
    return bool(_words(text) & receipt_keywords(receipts))


def is_follow_up(text: str) -> bool:
    """True if the question contains a cue word that refers back (FOLLOW_UP_CUES).

    Used only when the previous question was on topic, so "How much was that?" after
    a milk question reaches the model, but "Tell me a joke" does not. It looks back one
    question only; looking further back is a future enhancement.
    """
    return bool(_words(text) & FOLLOW_UP_CUES)


def mentions_own_name(text: str) -> bool:
    """True for 'My name is ...' and 'What's my name?', which count as on topic."""
    return "my name" in " ".join(text.lower().split())


PAYMENT_WORDS = frozenset({"pay", "paid", "payment"})
CARD_DETAIL_WORDS = frozenset({"number", "numbers", "pin", "cvv", "expiration", "expiry"})


def is_payment_method_question(text: str) -> bool:
    """True for 'Did I pay with a card at Walmart?': asks HOW a receipt was paid.

    The receipts record the payment method ("card" or "cash") but never card details,
    so this is a fair receipt question. Anything asking for card details (number, PIN,
    ...) is still treated as a card question.
    """
    words = _words(text)
    return bool(words & PAYMENT_WORDS) and not (words & CARD_DETAIL_WORDS)


def is_card_question(text: str) -> bool:
    """True if the question asks about card details; it gets CARD_INFO_MSG, not the model."""
    return bool(_words(text) & CARD_WORDS) and not is_payment_method_question(text)


def is_on_topic(session: Session, text: str) -> bool:
    """Should this question go to the model? See the checks above."""
    if is_receipt_question(text, session.receipts) or mentions_own_name(text):
        return True
    return session.last_was_receipt and is_follow_up(text)


def steering_message(receipts: list[dict]) -> str:
    """Explain the bot's scope, with stores and example questions taken from the data."""
    stores = [r["store"] for r in receipts]
    store_list = stores[0] if len(stores) == 1 else ", ".join(stores[:-1]) + " and " + stores[-1]
    first, second = receipts[0], receipts[1 % len(receipts)]
    item = _item_noun(first["items"][0]).lower()
    return (
        f"I can only help with your saved receipts from {store_list}. Try asking: "
        f'"How much was the {item} at {first["store"]}?" or '
        f'"What was my total at {second["store"]} on {second["date"]}?"'
    )


# --- Routing ---------------------------------------------------------------------

def ask(session: Session, question: str) -> Reply:
    """Send a question to the model. reply() appends the question and answer to history."""
    return Reply(session.bot.reply(question))


def handle_input(session: Session, raw: str) -> Reply:
    """Process one line of user input. Invalid input is never added to history."""
    try:
        text = validate_input(raw)
    except InvalidInputError as e:
        return Reply(str(e))

    if text.startswith("/"):
        name, arg = parse_command(text)
        command = COMMANDS.get(name)
        if command is None:
            return Reply(UNKNOWN_COMMAND_MSG.format(cmd=name))
        return command.handler(session, arg)

    # Steering: card questions and off-topic questions never reach the model and
    # are never added to history.
    if is_card_question(text):
        return Reply(CARD_INFO_MSG)
    on_topic = is_on_topic(session, text)
    session.last_was_receipt = on_topic
    if not on_topic:
        return Reply(steering_message(session.receipts))
    return ask(session, text)


def main() -> int:
    try:
        session = new_session()
    except ReceiptDataError as e:
        print(f"ReceiptBot can't start: {e}")
        return 1
    print("ReceiptBot is ready. Ask about your receipts, or type /help for commands.\n")
    while True:
        try:
            raw = input("you > ")
        except (EOFError, KeyboardInterrupt):
            # Ctrl+D / Ctrl+C: leave cleanly instead of crashing with a traceback.
            print("\nGoodbye!")
            return 0
        reply = handle_input(session, raw)
        print(f"bot > {reply.text}\n")
        if not reply.keep_running:
            return 0


if __name__ == "__main__":  # `python -m project2.receipt_bot`
    raise SystemExit(main())
