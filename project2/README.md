# Project 2: ReceiptBot refactor, save/load, and error handling

Project 2 continues the [Project 1 ReceiptBot](../README.md#project-1-receiptbot-my-assistant).
**Everything for Project 2 is in this `project2/` folder.** Project 1's files were not changed, so
they can still be graded as submitted. Project 2 reuses two Project 1 pieces as-is:
the assistant profile (`ribot/receipt_profile.py`) and the starter `ChatBot` class (`ribot/chatbot.py`).

Run from the repository root (offline, no API key needed):

```text
python -m project2.receipt_bot          # chat with ReceiptBot (now with /save and /load)
python -m pytest project2/tests         # run the Project 2 tests (68 tests)
```

**Study guide:** [STUDY_GUIDE.md](../STUDY_GUIDE.md) (in the main folder) explains every function in Projects 1 and 2 and
each Python technique they use, tagged by where it appears in the course.

## Where each requirement is

| Requirement | Where |
|---|---|
| Identify repeated or tightly coupled logic | [What I found](#1-what-i-found-in-the-project-1-code) below |
| Refactor into functions with clear inputs, outputs, responsibilities; keep memory | [`receipt_bot.py`](receipt_bot.py), [`receipts.py`](receipts.py), [function contracts](#2-function-contracts) below |
| Error handling for invalid input / malformed data | Malformed receipts file: [`receipts.py`](receipts.py). Corrupted or unsafe conversation files: [`conversation_store.py`](conversation_store.py). Empty and too-long input: `validate_input()` |
| Serialize a conversation and read it back | `/save` and `/load` commands; [`conversation_store.py`](conversation_store.py) |
| Tests | [`tests/`](tests/): 68 tests for refactored functions, memory, save/load round trips, and malformed files |
| One design choice and one limitation | [Design choices](#3-design-choices) and [Limitations](#4-limitations) below |

## Example session

```text
you > My name is Mike.
bot > Nice to meet you, Mike! ...
you > /save demo
bot > Saved 2 message(s) to conversations/demo.json.
you > /exit

(program restarted)

you > /load demo
bot > Loaded 2 message(s) from conversations/demo.json.
you > What is my name?
bot > You told me earlier — your name is Mike. ...
you > /load ../etc
bot > Not loaded: Invalid name '../etc'. Use 1-40 letters, numbers, '-' or '_' (no spaces or dots).
```

## 1. What I found in the Project 1 code

| # | Problem in Project 1 | Why it matters | Fix in Project 2 |
|---|---|---|---|
| 1 | **Commands were defined twice**: once in a `COMMANDS` dict (for `/help`) and again in an `if cmd == ...` chain in `handle_input()`. | Adding a command took two edits, and the help text could drift from what actually works. | One table, `COMMANDS`, maps each name to a description *and* a handler function. `/help` is generated from it. |
| 2 | **`handle_input()` did three jobs**: checking input, running commands, and talking to the model. | Hard to test or change one part without the others. | Split into `validate_input()`, `parse_command()`, one `cmd_*()` handler per command, and `ask()`. `handle_input()` only routes. |
| 3 | **Receipts were re-read from disk** every time the prompt was built and every time `/receipts` ran, using a hard-coded path. | The bot was tied to one file; tests could not supply different data. | Receipts load once in `new_session()` and are stored in a `Session`. Tests pass their own receipts and a temporary save folder. |
| 4 | **The receipt loader trusted the file.** A missing field caused a `KeyError` deep inside formatting code. | A typo in the data crashed the program with a confusing traceback. | `validate_receipts()` checks every field and raises `ReceiptDataError` naming the receipt and field. `main()` prints it and exits cleanly. |
| 5 | **The starter `ChatBot` keeps the conversation twice** (`history` and `logger.turns`), and `reset()` only clears `history`. | Two copies of memory can disagree. | Project 2 treats `bot.history` as the single source of truth; save/load and `/history` use only that. (The starter class was left unchanged; see limitations.) |

## 2. Function contracts

Each function has one job. Functions that can fail raise a specific error type; only the command
handlers and `main()` turn errors into messages for the user.

| Function | Input | Output | Raises |
|---|---|---|---|
| `receipts.load_receipts(path)` | path to JSON file | list of validated receipts | `ReceiptDataError` (missing file, bad JSON, missing/invalid fields) |
| `receipts.validate_receipts(data)` | parsed JSON | the same list | `ReceiptDataError` |
| `receipt_bot.new_session(receipts=None, conversations_dir=...)` | optional receipts and save folder | `Session` with a bot whose history is `[system message]` | `ReceiptDataError` if receipts must be loaded and are bad |
| `receipt_bot.validate_input(raw)` | raw text typed by user | cleaned text | `InvalidInputError` (empty, over 500 characters) |
| `receipt_bot.parse_command(text)` | `"/save october"` | `("/save", "october")` | — |
| `receipt_bot.handle_input(session, raw)` | session, raw text | `Reply(text, keep_running)` | never; all errors become a reply |
| `receipt_bot.restore_turns(session, turns)` | session, saved turns | none; history becomes `[current system message] + turns` | — |
| `conversation_store.conversation_path(name, folder)` | short name | `folder/name.json` | `ConversationFileError` (unsafe name) |
| `conversation_store.save_conversation(history, path)` | full history, path | path written | `OSError` if the disk write fails |
| `conversation_store.load_conversation(path)` | path | list of user/assistant turns | `ConversationFileError` (missing, bad JSON, wrong version, bad messages) |

**Memory behavior is preserved:** every question still goes through `ChatBot.reply()`, which appends
the question and answer to `history` and sends the whole list to the model. Tests confirm the bot
recalls earlier turns before and after a save/load, including in a brand-new session.

## 3. Design choices

**Save only the conversation, not the system prompt.** A saved file holds just the user and assistant
turns. On `/load`, they are placed behind a freshly built system message (the current profile and receipts).
- *Why:* files stay small and readable, and a loaded conversation always follows the current rules and
  receipts. It also blocks a hand-edited file from slipping in new instructions: `load_conversation()`
  rejects any message whose role is not `user` or `assistant`.

**One command table.** `COMMANDS` holds each command's description and handler together, so `/help`
can never list a command that doesn't exist, and adding a command is one entry plus one function.

**Fail without losing work.** If `/load` fails (missing file, corrupted JSON, wrong format), the
current conversation is left exactly as it was. Invalid input and commands are never added to history.

**Safe file names.** `/save` and `/load` accept only letters, numbers, `-` and `_`, so a name like
`../outside` cannot write or read files outside `project2/conversations/`. That folder is ignored by
Git because saved conversations could contain personal questions.

## 4. Limitations

- **A loaded conversation may not match changed receipts.** Because the system prompt is rebuilt from
  the *current* receipts, an old answer in a loaded conversation (for example, "milk was $3.49") can
  disagree with the receipts if the data file was edited since the save. The file records `saved_at`
  but not which receipts were used.
- **History grows without limit.** Every turn is sent to the model each time. A very long conversation
  will eventually exceed the model's context window; there is no trimming or summarizing yet.
- **All receipts go into the prompt.** This works for 3 receipts and 15 items, but would not scale to
  hundreds of receipts; that would need the retrieval (search) approach from later weeks.
- **Saves overwrite without asking.** `/save october` replaces an existing `october.json` silently,
  and saved files are plain, unencrypted JSON.
- **The starter `ChatBot` still has two copies of memory.** Its `logger.turns` is not cleared by
  `reset()` or updated by `/load`. Project 2 never reads the logger, but the class itself was not fixed
  because it belongs to the course starter.
- **Offline mode doesn't really read receipts.** Without an API key, the stand-in model gives
  placeholder answers (it only demonstrates memory with "my name is ..."). Real answers need a key in `.env`.
