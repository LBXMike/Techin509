"""Tests for loading receipts, including malformed receipt files."""

import copy
import json

import pytest

from project2.receipt_bot import main
from project2.receipts import ReceiptDataError, load_receipts, validate_receipts

GOOD = load_receipts()


def write_receipts(path, receipts):
    path.write_text(json.dumps({"receipts": receipts}), encoding="utf-8")
    return path


def broken(change):
    """A deep copy of the real receipts with one change applied to the first receipt."""
    receipts = copy.deepcopy(GOOD)
    change(receipts[0])
    return receipts


def test_real_receipts_pass_validation():
    assert validate_receipts(copy.deepcopy(GOOD)) == GOOD


def test_missing_file(tmp_path):
    with pytest.raises(ReceiptDataError, match="not found"):
        load_receipts(tmp_path / "nope.json")


def test_invalid_json_reports_line(tmp_path):
    path = tmp_path / "r.json"
    path.write_text('{"receipts": [\n  {"id": "R1",\n}', encoding="utf-8")
    with pytest.raises(ReceiptDataError, match=r"not valid JSON \(line \d+"):
        load_receipts(path)


def test_missing_top_level_key(tmp_path):
    path = tmp_path / "r.json"
    path.write_text(json.dumps({"items": []}), encoding="utf-8")
    with pytest.raises(ReceiptDataError, match="top-level 'receipts'"):
        load_receipts(path)


def test_empty_receipts_list(tmp_path):
    with pytest.raises(ReceiptDataError, match="non-empty list"):
        load_receipts(write_receipts(tmp_path / "r.json", []))


@pytest.mark.parametrize(
    "change, error",
    [
        (lambda r: r.pop("store"), "R1 is missing: store"),
        (lambda r: r.update(total="20.11"), "'total' must be a non-negative number"),
        (lambda r: r.update(tax=-1), "'tax' must be a non-negative number"),
        (lambda r: r.update(items=[]), "'items' must be a non-empty list"),
        (lambda r: r["items"][0].pop("name"), "every item needs a text 'name'"),
        (lambda r: r["items"][0].update(price="3.49"), "invalid price '3.49'"),
        (lambda r: r["items"][0].update(price=True), "invalid price True"),
    ],
)
def test_malformed_receipt_names_the_problem(tmp_path, change, error):
    path = write_receipts(tmp_path / "r.json", broken(change))
    with pytest.raises(ReceiptDataError, match=error):
        load_receipts(path)


def test_bot_exits_cleanly_when_receipts_are_broken(monkeypatch, capsys):
    def bad_load():
        raise ReceiptDataError("Receipt R1 is missing: store.")

    monkeypatch.setattr("project2.receipt_bot.load_receipts", bad_load)
    assert main() == 1
    assert "can't start: Receipt R1 is missing: store." in capsys.readouterr().out
