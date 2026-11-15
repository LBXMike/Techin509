"""Week 7 owner acceptance tests: look up purchased items by name.

Run from the repository root:
    python -m pytest project2/tests/test_p2_item_lookup.py -v

Synthetic sample data: project2/tests/data/item_lookup_sample.json
The developer implements project2.item_lookup.find_item().
These tests are committed before the implementation (test-first), so they
fail with ModuleNotFoundError until project2/item_lookup.py exists.
"""

import copy
from pathlib import Path

from project2.receipts import load_receipts

SAMPLE = Path(__file__).parent / "data" / "item_lookup_sample.json"
RECEIPTS = load_receipts(SAMPLE)


# Normal case: a match in more than one receipt, any capitalisation.
def test_finds_item_in_every_receipt_case_insensitively_in_order():
    from project2.item_lookup import find_item

    assert find_item("MILK", RECEIPTS) == [
        {"receipt": "R1", "store": "Walmart", "date": "2026-10-01",
         "item": "Milk, whole, 1 gallon", "price": 3.49},
        {"receipt": "R3", "store": "Safeway", "date": "2026-10-15",
         "item": "Milk, 2%, half gallon", "price": 2.29},
    ]


# Normal case: a different item, so the answer is not hardcoded to "milk".
def test_finds_single_item_by_partial_name():
    from project2.item_lookup import find_item

    assert find_item("tooth", RECEIPTS) == [
        {"receipt": "R2", "store": "Target", "date": "2026-10-08",
         "item": "Toothpaste", "price": 3.59},
    ]


# Edge case: nothing was bought with that name.
def test_unknown_item_returns_empty_list():
    from project2.item_lookup import find_item

    assert find_item("motor oil", RECEIPTS) == []


# Edge case: a blank search finds nothing instead of every item.
def test_blank_or_whitespace_query_returns_empty_list():
    from project2.item_lookup import find_item

    assert find_item("", RECEIPTS) == []
    assert find_item("   ", RECEIPTS) == []


# Edge case: looking something up must not change the receipts.
def test_lookup_does_not_change_receipts():
    from project2.item_lookup import find_item

    before = copy.deepcopy(RECEIPTS)
    find_item("milk", RECEIPTS)
    assert RECEIPTS == before
