# Feature request: steer off-topic questions back to the receipts

**Requested by:** Mike **Built by:** ____________________ **Date:** ____________

## The problem

ReceiptBot answers questions about 3 saved receipts in
[`data/receipts/receipts.json`](../data/receipts/receipts.json) (Walmart, Target, Safeway).
Right now, **nothing in the code checks whether a question is about the receipts.** Every
question goes straight to the model, and the only guard is one line in the system prompt
("Do not answer questions unrelated to the user's receipts"). So:

- With no API key, `"What's the capital of France?"` gets the same placeholder reply as a real question.
- With a key, staying on topic depends on the model following that one instruction.
- Off-topic questions are sent to the API (using credits) and saved in the history.

## The feature

Add a **steering function** that catches off-topic questions *before* they reach the model.
It should reply with a short message that asks the user for a receipt question and suggests
**example questions built from the receipts JSON**, not hard-coded text. For example:

```text
you > What's the capital of France?
bot > I can only help with your saved receipts. Try asking something like:
        - How much was the Milk, whole, 1 gallon at Walmart?
        - What did I buy at Target on 2026-10-08?
        - What was the total at Safeway?
```

If the receipts file changes (a new store or item), the suggestions should change with it.

## Where to build it

Build on **Project 2** ([`project2/receipt_bot.py`](../project2/receipt_bot.py)). Its code is
already split into small functions, and `session.receipts` gives you the loaded receipt data.
Don't change the `ribot/` folder (Project 1 has been submitted).

Suggested design (you can change it if you explain why):

| Function | Input | Output | Job |
|---|---|---|---|
| `is_receipt_question(text, receipts)` | the user's question, the receipts list | `bool` | `True` if the question looks like it's about the receipts |
| `steering_message(receipts)` | the receipts list | `str` | The reply above, with examples taken from the receipts |

Call them in `handle_input()`, just before `ask()`. If the question is off topic, return
`Reply(steering_message(...))` without calling the model.

**How to decide "on topic":** one simple approach is a set of words taken from the JSON
(store names, item words like "milk" or "shampoo", dates) plus general receipt words
("total", "price", "cost", "spend", "buy", "receipt", "tax"). Lowercase everything and match
whole words. Keep it simple and explainable; perfect accuracy isn't the goal.

## Acceptance criteria

- [ ] `"What's the capital of France?"` and `"Tell me a joke"` get the steering message.
- [ ] `"How much was the milk?"`, `"What did I buy at Target?"`, `"What was my total on 2026-10-15?"` still go to the model.
- [ ] The steering examples come from the receipts data (a test with different receipts gets different examples).
- [ ] Off-topic questions are **not** sent to the model and **not** added to `session.bot.history`.
- [ ] Commands (`/help`, `/receipts`, ...) and the empty/too-long checks still work as before.
- [ ] New tests in `project2/tests/test_p2_steering.py`, and all existing tests still pass.
- [ ] A short note at the end of [`project2/README.md`](../project2/README.md): what you built, and one limitation (for example, a question it gets wrong).

## Running it

From the repo root (see the main README for the uv setup):

```text
python -m project2.receipt_bot
python -m pytest project2/tests
```

**Run the tests with the API key turned off.** The tests expect offline mode; with a key in
`.env` they call the real API and fail. Comment out the `OPENAI_API_KEY=` line in `.env`
first. Keep the class key only in `.env` (git ignores it), and never commit or paste it.

## When you're done

Push your work to a branch named `feature/steering` and open a pull request, or send me the
changed files. Tell me which acceptance criteria you met.
