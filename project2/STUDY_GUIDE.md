# ReceiptBot study guide: functions and techniques (Projects 1 & 2)

A refresher on every function in ReceiptBot and the Python techniques behind them.
Each technique is tagged with where it comes from in this course:

- **[Lesson Wk N]**: taught in that week's lesson or optional reading
- **[Starter]**: not in a lesson yet, but used in the course's `rag-starter` code
- **[New]**: not used anywhere else in the course repo; worth knowing how to explain

Contents:
1. [How a message flows](#1-how-a-message-flows)
2. [Project 1 functions](#2-project-1-functions)
3. [Project 2 functions](#3-project-2-functions)
4. [Techniques explained](#4-techniques-explained)
5. [Testing techniques](#5-testing-techniques)
6. [Self-check questions](#6-self-check-questions)

---

## 1. How a message flows

**Project 1** (`python -m ribot.receipt_bot`):

```text
main()  ── reads a line ──>  handle_input(bot, raw)
                               ├─ empty / too long?   -> message, nothing saved
                               ├─ starts with "/"?    -> if/elif chain runs the command
                               └─ otherwise           -> bot.reply(text)
                                                         ├─ history.append(user message)
                                                         ├─ chat(history)  (the model sees everything)
                                                         └─ history.append(assistant answer)
```

**Project 2** (`python -m project2.receipt_bot`) does the same job, split into smaller pieces:

```text
main()  ── reads a line ──>  handle_input(session, raw)
                               ├─ validate_input(raw)        raises InvalidInputError -> message
                               ├─ parse_command(text)        "/save oct" -> ("/save", "oct")
                               │    └─ COMMANDS[name].handler(session, arg)   e.g. cmd_save
                               └─ ask(session, text)         -> session.bot.reply(text)
```

**Memory** in both projects is `bot.history`, a list of dicts:

```python
[
    {"role": "system",    "content": "You are ReceiptBot ... Receipts: ..."},  # always first
    {"role": "user",      "content": "How much did the milk cost?"},
    {"role": "assistant", "content": "Milk was $3.49 at Walmart ..."},
]
```

The whole list is sent to the model on every turn. That is the only reason the bot "remembers".

---

## 2. Project 1 functions

### [`ribot/receipt_profile.py`](../ribot/receipt_profile.py): the assistant's personality

| Function | Input | Output | What it does |
|---|---|---|---|
| `_bullets(items)` | list of strings | one string | Turns `["a", "b"]` into `"- a\n- b"`. The leading `_` means "private helper, only used in this file". |
| `build_profile_prompt(profile, receipts_text="")` | profile dict, optional receipts text | system prompt string | Fills an f-string template with the role, tone, rules, answer requirements, and boundaries, then adds the receipts if given. |

`RECEIPT_PROFILE` is plain data (a dict of strings and lists), so each part can be changed or tested on its own.

### [`ribot/receipts.py`](../ribot/receipts.py): Project 1 receipt loading

| Function | Input | Output | What it does |
|---|---|---|---|
| `load_receipts(path)` | file path (has a default) | list of receipt dicts | Opens the JSON file and returns `data["receipts"]`. No checking: a bad file crashes. |
| `format_receipt(receipt)` | one receipt dict | multi-line string | Store/date line, one line per item, then subtotal/tax/total. |
| `format_receipts(receipts)` | list of receipts | string | Calls `format_receipt` on each, joined by blank lines. |
| `receipts_summary(receipts)` | list of receipts | string | One short line per receipt, for `/receipts`. |

### [`ribot/receipt_bot.py`](../ribot/receipt_bot.py): Project 1 command loop

| Function | Input | Output | What it does |
|---|---|---|---|
| `system_prompt()` | nothing | string | Loads receipts from disk and builds the full prompt. |
| `new_bot()` | nothing | `ChatBot` | Creates a bot whose first history message is that prompt. |
| `help_text()` | nothing | string | Lists commands from the `COMMANDS` dict. |
| `history_text(bot)` | bot | string | Numbered list of history messages; shortens the long system message. |
| `handle_input(bot, raw)` | bot, raw text | `(text, keep_running)` tuple | Checks empty/too-long, runs commands with `if`/`elif`, otherwise asks the bot. |
| `main()` | nothing | nothing | The `while True` loop: `input()`, `handle_input()`, `print()`, stop on `/exit` or Ctrl+C. |

### [`ribot/chatbot.py`](../ribot/chatbot.py): course starter, used by both projects

| Method | What it does |
|---|---|
| `ChatBot(system_prompt)` | Starts `self.history` with one system message. |
| `add_turn(role, content)` | Appends one message to `history` (and to the logger). |
| `reply(user_message)` | `add_turn("user", ...)`, calls `chat(self.history)`, `add_turn("assistant", answer)`, returns the answer. **This is where memory happens.** |
| `reset()` | Keeps only `history[:1]` (the system message). |

---

## 3. Project 2 functions

### [`project2/receipts.py`](receipts.py): loading with validation

| Function | Input | Output | Raises | What it does |
|---|---|---|---|---|
| `_is_money(value)` | anything | `True`/`False` | — | True for non-negative `int`/`float`, but not `True`/`False` (see [bool trap](#the-bool-trap)). |
| `validate_receipts(receipts)` | parsed JSON | same list | `ReceiptDataError` | Checks every receipt has all fields, money fields are numbers, every item has a name and price. |
| `load_receipts(path)` | file path | validated list | `ReceiptDataError` | Opens the file, turns "file not found" and "bad JSON" into clear messages, then validates. |
| `format_receipt`, `format_receipts`, `receipts_summary` | (same as Project 1) | | — | Unchanged formatting helpers. |

### [`project2/conversation_store.py`](conversation_store.py): save and load

| Function | Input | Output | Raises | What it does |
|---|---|---|---|---|
| `conversation_path(name, folder)` | short name | `folder/name.json` | `ConversationFileError` | Only allows letters, numbers, `-`, `_`, so `../outside` can't escape the folder. |
| `turns_only(history)` | full history | list of user/assistant messages | — | Drops the system message (it is rebuilt on load). |
| `validate_messages(messages)` | parsed JSON | same list | `ConversationFileError` | Each message must have exactly `role` and `content`; role must be `user` or `assistant`. |
| `save_conversation(history, path)` | history, path | the path | `OSError` | Writes `{"format_version": 1, "saved_at": ..., "messages": [...]}`. Creates the folder if needed. |
| `load_conversation(path)` | path | list of turns | `ConversationFileError` | Reads the file; rejects missing files, bad JSON, wrong version, bad messages. |

### [`project2/receipt_bot.py`](receipt_bot.py): the refactored loop

**Building a session**

| Function | Input | Output | What it does |
|---|---|---|---|
| `build_system_prompt(receipts)` | receipts | string | Profile + formatted receipts. Receipts are passed in, not read from disk. |
| `new_session(receipts=None, conversations_dir=...)` | optional receipts and folder | `Session` | Loads receipts once (unless given), creates the bot. Tests pass their own receipts and a temp folder. |
| `restore_turns(session, turns)` | session, saved turns | nothing (changes history) | `history = [current system message] + turns`. |

**Checking input**

| Function | Input | Output | Raises | What it does |
|---|---|---|---|---|
| `validate_input(raw)` | raw text | stripped text | `InvalidInputError` | Rejects empty/whitespace and anything over 500 characters. |
| `parse_command(text)` | `"/SAVE oct"` | `("/save", "oct")` | — | Splits at the first space and lowercases the command name. |

**Command handlers**: all have the same shape, `(session, arg) -> Reply`

| Handler | Command | What it does |
|---|---|---|
| `cmd_help` | `/help` | Builds the list from the `COMMANDS` table. |
| `cmd_receipts` | `/receipts` | `receipts_summary(session.receipts)`. |
| `cmd_history` | `/history` | Numbered history; counts questions with `turns_only`. |
| `cmd_reset` | `/reset` | `session.bot.reset()`. |
| `cmd_save` | `/save [name]` | `conversation_path` + `save_conversation`; errors become "Not saved: ...". |
| `cmd_load` | `/load [name]` | `conversation_path` + `load_conversation` + `restore_turns`; on error the current chat is untouched. |
| `cmd_exit` | `/exit` | `Reply("Goodbye!", keep_running=False)`. |

**Routing**

| Function | Input | Output | What it does |
|---|---|---|---|
| `ask(session, question)` | session, text | `Reply` | Sends the question through `bot.reply()` (memory updated there). |
| `handle_input(session, raw)` | session, raw text | `Reply` | Validate → command lookup in `COMMANDS` → or `ask`. Never raises; every error becomes a reply. |
| `main()` | nothing | exit code `0` or `1` | Builds the session (prints a clear error and returns `1` if receipts are broken), then loops. |

**Data types**

| Name | Kind | Holds |
|---|---|---|
| `Reply` | `NamedTuple` | `text`, `keep_running` (default `True`) |
| `Command` | `NamedTuple` | `description`, `handler` (a function) |
| `Session` | `@dataclass` | `bot`, `receipts`, `conversations_dir` |
| `COMMANDS` | dict | `"/help" -> Command(...)`, one entry per command |

---

## 4. Techniques explained

### Basics used throughout

| Technique | Source | Where | One-line reminder |
|---|---|---|---|
| Functions with type hints | [Lesson Wk 3–4] | everywhere | `def f(x: str) -> int:` hints say what goes in and out; Python doesn't enforce them. |
| f-strings and format specs | [Lesson Wk 2] | formatting | `f"${price:.2f}"` → `$3.49`; `f"{name:<10}"` pads to 10 characters; `f"{x!r}"` shows quotes, like `'3.49'`. |
| List of dicts | [Lesson Wk 3] | history, receipts | `[{"role": "user", "content": "hi"}]` |
| `try` / `except` | [Lesson Wk 2, 4–6] | loading, saving | Catch a specific error and respond instead of crashing. |
| JSON `load` / `dump` | [Lesson Wk 4] | receipts, saves | `json.load(f)` file → Python; `json.dump(data, f, indent=2)` Python → file. |
| `json.JSONDecodeError` | [Lesson Wk 4] | both loaders | Raised for broken JSON; has `.lineno` and `.colno` for the error location. |
| Regex `re.compile` | [Lesson Wk 3] | `conversation_path` | `^[A-Za-z0-9_-]{1,40}$` = whole string is 1–40 safe characters. |
| `pathlib.Path` | [Lesson Wk 1, 5–6] | file paths | `folder / "name.json"` joins paths; `.mkdir(parents=True, exist_ok=True)`. |
| `datetime` | [Lesson Wk 4–5] | `save_conversation` | `datetime.now().isoformat(timespec="seconds")` → `"2026-11-05T14:03:00"`. |
| `with open(...)` | [Lesson Wk 4] | file I/O | Closes the file automatically, even after an error. |
| Classes and methods | [Lesson Wk 3] | `ChatBot` | `self.history` is data that belongs to one bot. |
| `raise SystemExit(main())` | [Lesson Wk 5] | end of `receipt_bot.py` | Uses `main()`'s return value (0 = OK, 1 = error) as the program's exit code. |

### From the course starter code

**`from __future__ import annotations`** [Starter]
Top of every file. Lets type hints like `list[dict]` or `Session` (defined later in the file) work
without errors. It has no effect on how the code runs.

**`Callable` type hint** [Starter]

```python
handler: Callable[[Session, str], Reply]
```

Read it as: "a function that takes a `Session` and a `str` and returns a `Reply`."

**`@dataclass`** [Starter]

```python
@dataclass
class Session:
    bot: ChatBot
    receipts: list[dict]
    conversations_dir: Path = field(default=CONVERSATIONS_DIR)
```

A shortcut for a class that mostly holds data. Python writes `__init__` for you, so
`Session(bot=b, receipts=r)` just works. `field(default=...)` gives a field a default value.
Why use it: one object carries everything a conversation needs, instead of passing three
arguments to every function.

### New in Project 2

**`NamedTuple`** [New]

```python
class Reply(NamedTuple):
    text: str
    keep_running: bool = True

r = Reply("Goodbye!", keep_running=False)
r.text            # "Goodbye!"   (read by name)
text, keep = r    # still unpacks like a normal tuple
```

A tuple whose positions have names. Project 1 returned `(text, True)`, where you had to remember
which position meant what. `Reply` keeps the same shape but is self-explaining. Like any tuple,
it can't be changed after it is created.

**Custom exception classes** [New]

```python
class ReceiptDataError(ValueError):
    """The receipts file is missing, is not valid JSON, or has the wrong shape."""

raise ReceiptDataError("Receipt R1 is missing: store.")
...
except ReceiptDataError as e:
    print(f"ReceiptBot can't start: {e}")
```

A new error type made by inheriting from a built-in one (`ValueError`). The body is just a
docstring, with nothing else needed. Why: `except ReceiptDataError` catches *only* our data
problems, not unrelated bugs that also happen to raise `ValueError` or `KeyError`.
Project 2 has three: `ReceiptDataError`, `ConversationFileError`, `InvalidInputError`.

**The pattern: raise deep, catch at the edge.** Small functions (`validate_input`,
`load_conversation`) only *raise*. The command handlers and `main()` *catch* and turn errors
into friendly messages. Small functions stay simple and testable; user-facing wording lives in one layer.

**`raise ... from None`** [New]

```python
except FileNotFoundError:
    raise ReceiptDataError(f"Receipts file not found: {path}") from None
```

Raising inside an `except` normally prints *both* errors ("During handling of the above
exception, another exception occurred..."). `from None` hides the original so the user sees only
the clear message. Behavior is otherwise identical.

**Functions stored in a dictionary (dispatch table)** [New]

```python
COMMANDS = {
    "/help": Command("show this list of commands", cmd_help),   # cmd_help, no ()
    ...
}
command = COMMANDS.get(name)          # look up by name; None if unknown
return command.handler(session, arg)  # handler IS cmd_help, so this calls it
```

In Python, a function is a value like any other. `cmd_help` (no parentheses) is the function
itself; `cmd_help(...)` calls it. Storing functions in a dict replaces a long `if`/`elif` chain,
and because `/help` reads the same dict, the help text can never list a command that doesn't exist.
This is the main fix for "commands defined in two places".

**`str.partition`** [New]

```python
"/save october".partition(" ")   # ('/save', ' ', 'october')
"/help".partition(" ")           # ('/help', '', '')
name, _, arg = text.partition(" ")
```

Splits at the *first* separator and always returns exactly 3 parts, so unpacking never fails.
`_` is the usual name for "a value I don't need". `text.split(" ", 1)` is the closest
alternative but returns only 1 part when there is no space.

**Comparing dict keys as a set** [New]

```python
set({"role": "user", "content": "hi"})   # {'role', 'content'}
set(msg) != {"role", "content"}           # True if any key is missing OR extra
```

`set(a_dict)` gives its keys. Comparing sets ignores order and checks for an *exact* match, which
catches both missing and extra fields in one line.

<a id="the-bool-trap"></a>
**The bool trap** [New]

```python
isinstance(True, int)   # True! In Python, bool is a kind of int (True == 1)
isinstance(value, (int, float)) and not isinstance(value, bool)
```

Without the second check, a price of `true` in the JSON would pass as `$1.00`.

**Dependency injection (passing things in)** [design idea]
`new_session(receipts=None, conversations_dir=...)` takes its data and save folder as arguments
instead of always reading fixed locations. The real program uses the defaults; tests pass fake
receipts and a temporary folder. This replaced Project 1's `system_prompt()`, which always read the file.

**Copying dicts: `dict(m)`** [Lesson Wk 3 idea]
`turns_only` and `restore_turns` build new dicts with `dict(m)`, so changing a saved copy never
changes the live history (and the reverse).

---

## 5. Testing techniques

| Technique | Source | Example from the tests |
|---|---|---|
| `assert` | [Lesson Wk 6] | `assert reply.keep_running is False` |
| `pytest.raises` | [Lesson Wk 6] | `with pytest.raises(InvalidInputError, match="too long"):` (the block must raise; `match` checks the message with regex) |
| `@pytest.fixture` | [Starter] | `def session(tmp_path): return new_session(conversations_dir=tmp_path)`. Any test with a `session` parameter gets a fresh one. |
| `tmp_path` | [Starter] | Built-in fixture: an empty temporary folder per test, so saves never touch real files. |
| `@pytest.mark.parametrize` | [Starter] | Runs one test once per input: `@pytest.mark.parametrize("raw", ["", "   ", "\t\n"])`. |
| `monkeypatch` | [Starter] | `monkeypatch.setattr("project2.receipt_bot.load_receipts", bad_load)` swaps a function for one test only, to simulate a broken file. |
| `capsys` | [Starter] | Captures `print()` output: `capsys.readouterr().out`. |
| `lambda` | [Lesson Wk 5–6] | `lambda r: r.pop("store")`: a tiny unnamed function; the tests use them to describe "break the receipt this way". |
| `copy.deepcopy` | [New] | Copies nested data fully, so breaking one test's copy never affects the real receipts or other tests. |
| `conftest.py` | [Lesson Wk 1–2] | Runs before the tests; adds the repo root to `sys.path` so `import project2` works. |

---

## 6. Self-check questions

<details><summary>1. Why does the bot remember earlier questions?</summary>

`ChatBot.reply()` appends each question and answer to `history`, and the *entire* list is sent to
the model every turn. Nothing else stores memory.
</details>

<details><summary>2. Why doesn't a saved file include the system prompt?</summary>

It is rebuilt from the current profile and receipts on `/load`. Files stay small, loaded chats use
current rules, and a hand-edited file can't add new instructions (`role: "system"` is rejected).
</details>

<details><summary>3. What is the difference between <code>cmd_help</code> and <code>cmd_help(session, "")</code>?</summary>

The first is the function itself (a value you can store in a dict); the second calls it and gives
back a `Reply`.
</details>

<details><summary>4. Why make <code>ReceiptDataError</code> instead of raising <code>ValueError</code>?</summary>

So `main()` can catch exactly "the receipts file is bad" and print a clear message, without
accidentally hiding unrelated bugs.
</details>

<details><summary>5. What happens if <code>/load</code> fails halfway?</summary>

`restore_turns` only runs after `load_conversation` succeeds, so a failure returns
"Not loaded: ..." and the current history is untouched.
</details>

<details><summary>6. What does <code>handle_input</code> return, and can it raise?</summary>

A `Reply(text, keep_running)`. It never raises: invalid input, unknown commands, and file problems
all come back as reply text.
</details>
