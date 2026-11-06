"""Project 1: the ReceiptBot command loop.

Run it:  python -m ribot.receipt_bot

How it works:
- The bot starts with the ReceiptBot profile as its system prompt (ribot/receipt_profile.py).
- Conversation history is `bot.history`: a list of {role, content} dicts. Every question
  and answer is appended, and the whole list is sent to the model each turn, so follow-up
  questions can refer to earlier ones.
- Commands start with "/". Anything else is a question for the assistant.
- Bad input (empty, whitespace-only, too long, or an unknown command) gets a clear message
  and is NOT added to history.
"""

from __future__ import annotations

from .chatbot import ChatBot
from .receipt_profile import build_profile_prompt

MAX_INPUT_CHARS = 500

COMMANDS = {
    "/help": "show this list of commands",
    "/history": "print the conversation history the model sees",
    "/reset": "clear the history and start a new conversation",
    "/exit": "quit ReceiptBot",
}

EMPTY_INPUT_MSG = "Please type a question about your receipts (or /help for commands)."
TOO_LONG_MSG = (
    f"That message is too long ({{n}} characters). Please keep questions under "
    f"{MAX_INPUT_CHARS} characters."
)
UNKNOWN_COMMAND_MSG = "Unknown command '{cmd}'. Type /help to see the commands."


def new_bot() -> ChatBot:
    """Create a ChatBot that uses the ReceiptBot profile."""
    return ChatBot(system_prompt=build_profile_prompt())


def help_text() -> str:
    return "Commands:\n" + "\n".join(f"  {cmd:<9} {desc}" for cmd, desc in COMMANDS.items())


def history_text(bot: ChatBot) -> str:
    """Show the history, one line per message. The long system prompt is shortened."""
    lines = []
    for i, msg in enumerate(bot.history):
        content = msg["content"]
        if msg["role"] == "system":
            content = content.splitlines()[0] + " ... (profile)"
        lines.append(f"  {i}. [{msg['role']}] {content}")
    turns = (len(bot.history) - 1) // 2
    lines.append(f"  ({turns} question(s) so far)")
    return "\n".join(lines)


def handle_input(bot: ChatBot, raw: str) -> tuple[str, bool]:
    """Process one line of user input.

    Returns (text to print, keep_running). keep_running is False only for /exit.
    """
    text = raw.strip()

    # Invalid input: empty or whitespace-only. Not sent to the model, not saved to history.
    if not text:
        return EMPTY_INPUT_MSG, True

    # Invalid input: too long to be a sensible receipt question.
    if len(text) > MAX_INPUT_CHARS:
        return TOO_LONG_MSG.format(n=len(text)), True

    if text.startswith("/"):
        cmd = text.split()[0].lower()
        if cmd == "/exit":
            return "Goodbye! Your conversation was not saved.", False
        if cmd == "/help":
            return help_text(), True
        if cmd == "/history":
            return history_text(bot), True
        if cmd == "/reset":
            bot.reset()
            return "History cleared. Starting a new conversation.", True
        return UNKNOWN_COMMAND_MSG.format(cmd=cmd), True

    # A normal question: reply() adds the question and the answer to history.
    return bot.reply(text), True


def main() -> None:
    bot = new_bot()
    print("ReceiptBot is ready. Ask about your receipts, or type /help for commands.\n")
    while True:
        try:
            raw = input("you > ")
        except (EOFError, KeyboardInterrupt):
            # Ctrl+D / Ctrl+C: leave cleanly instead of crashing with a traceback.
            print("\nGoodbye!")
            break
        output, keep_running = handle_input(bot, raw)
        print(f"bot > {output}\n")
        if not keep_running:
            break


if __name__ == "__main__":  # `python -m ribot.receipt_bot`
    main()
