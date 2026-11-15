"""Proposed acceptance tests for the steering check (issue #1).

Proposed by Florence (developer) for Mike (owner) to accept: one normal case, one edge case.
Run from the repo root, with OPENAI_API_KEY= commented out in .env:
    python -m pytest project2/tests/test_p2_steering.py -v
Data: data/receipts/receipts.json (synthetic), loaded by new_session().
"""

import pytest

from project2.receipt_bot import handle_input, new_session


@pytest.fixture
def session(tmp_path):
    """A fresh session that saves conversations into a temporary folder."""
    return new_session(conversations_dir=tmp_path)


def test_receipt_question_is_sent_to_the_model_and_saved(session):
    question = "How much was the milk at Walmart?"
    handle_input(session, question)
    assert session.bot.history[-2] == {"role": "user", "content": question}
    assert session.bot.history[-1]["role"] == "assistant"
    assert len(session.bot.history) == 1 + 2  # system + one (user, assistant) pair


def test_off_topic_question_gets_steering_message_and_is_not_saved(session):
    reply = handle_input(session, "What's the capital of France?")
    assert reply.text == (
        "I can only help with your saved receipts from Walmart, Target and Safeway. "
        'Try asking: "How much was the milk at Walmart?" or '
        '"What was my total at Target on 2026-10-08?"'
    )
    assert reply.keep_running
    assert len(session.bot.history) == 1  # only the system message


@pytest.mark.parametrize("question", [
    "How much did I pay?",
    "What's the cheapest item?",
    "Which store did I shop at?",
])
def test_general_receipt_words_reach_the_model(session, question):
    handle_input(session, question)
    assert session.bot.history[-2] == {"role": "user", "content": question}


def test_payment_method_question_reaches_the_model(session):
    question = "Did I pay with a card at Walmart?"
    handle_input(session, question)
    assert session.bot.history[-2] == {"role": "user", "content": question}


def test_card_number_question_is_still_blocked(session):
    reply = handle_input(session, "What card number did I pay with?")
    assert reply.text == "I don't store card information for safety reasons."
    assert len(session.bot.history) == 1
