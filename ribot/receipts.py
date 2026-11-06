"""Project 1: load the synthetic receipts and format them as text for the model.

The data is small (3 receipts, 15 items), so the whole set goes straight into the
system prompt. No search index is needed for this first version.
"""

from __future__ import annotations

import json
from pathlib import Path

RECEIPTS_PATH = Path(__file__).resolve().parent.parent / "data" / "receipts" / "receipts.json"


def load_receipts(path: Path = RECEIPTS_PATH) -> list[dict]:
    """Read the receipts JSON file and return the list of receipts."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)["receipts"]


def format_receipt(receipt: dict) -> str:
    """Turn one receipt dict into readable lines."""
    lines = [f"Receipt {receipt['id']}: {receipt['store']}, {receipt['date']}"]
    for item in receipt["items"]:
        lines.append(f"  - {item['name']}: ${item['price']:.2f}")
    lines.append(
        f"  Subtotal ${receipt['subtotal']:.2f} | Tax ${receipt['tax']:.2f} | "
        f"Total ${receipt['total']:.2f} | Paid by {receipt['payment']}"
    )
    return "\n".join(lines)


def format_receipts(receipts: list[dict]) -> str:
    """Format every receipt, separated by blank lines."""
    return "\n\n".join(format_receipt(r) for r in receipts)


def receipts_summary(receipts: list[dict]) -> str:
    """One line per receipt, for the /receipts command."""
    return "\n".join(
        f"  {r['id']}  {r['date']}  {r['store']:<8} {len(r['items'])} items  ${r['total']:.2f}"
        for r in receipts
    )
