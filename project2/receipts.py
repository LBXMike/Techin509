"""Load, check, and format the synthetic receipts.

Contract:
- load_receipts(path) -> list of receipt dicts, or raises ReceiptDataError with a
  message that says which file, receipt, and field is wrong.
- format_* functions only format; they assume the receipts already passed validation.

The data is small (3 receipts, 15 items), so the whole set goes straight into the
system prompt. No search index is needed for this first version.
"""

from __future__ import annotations

import json
from pathlib import Path

RECEIPTS_PATH = Path(__file__).resolve().parent.parent / "data" / "receipts" / "receipts.json"

REQUIRED_RECEIPT_FIELDS = ("id", "store", "date", "items", "subtotal", "tax", "total", "payment")


class ReceiptDataError(ValueError):
    """The receipts file is missing, is not valid JSON, or has the wrong shape."""


def _is_money(value: object) -> bool:
    # bool is a subclass of int in Python, so rule it out explicitly.
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def validate_receipts(receipts: object) -> list[dict]:
    """Check every receipt has the fields and types the bot relies on.

    Returns the same list if it is valid; raises ReceiptDataError on the first problem.
    """
    if not isinstance(receipts, list) or not receipts:
        raise ReceiptDataError("'receipts' must be a non-empty list.")

    for n, receipt in enumerate(receipts, start=1):
        if not isinstance(receipt, dict):
            raise ReceiptDataError(f"Receipt #{n} is not an object.")
        label = receipt.get("id", f"#{n}")
        missing = [f for f in REQUIRED_RECEIPT_FIELDS if f not in receipt]
        if missing:
            raise ReceiptDataError(f"Receipt {label} is missing: {', '.join(missing)}.")
        for field in ("subtotal", "tax", "total"):
            if not _is_money(receipt[field]):
                raise ReceiptDataError(
                    f"Receipt {label}: '{field}' must be a non-negative number, "
                    f"got {receipt[field]!r}."
                )
        items = receipt["items"]
        if not isinstance(items, list) or not items:
            raise ReceiptDataError(f"Receipt {label}: 'items' must be a non-empty list.")
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                raise ReceiptDataError(f"Receipt {label}: every item needs a text 'name'.")
            if not _is_money(item.get("price")):
                raise ReceiptDataError(
                    f"Receipt {label}: item {item['name']!r} has an invalid price "
                    f"{item.get('price')!r}."
                )
    return receipts


def load_receipts(path: Path = RECEIPTS_PATH) -> list[dict]:
    """Read and validate the receipts file."""
    path = Path(path)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise ReceiptDataError(f"Receipts file not found: {path}") from None
    except json.JSONDecodeError as e:
        raise ReceiptDataError(
            f"Receipts file {path.name} is not valid JSON (line {e.lineno}, column {e.colno})."
        ) from None
    if not isinstance(data, dict) or "receipts" not in data:
        raise ReceiptDataError(f"Receipts file {path.name} needs a top-level 'receipts' list.")
    return validate_receipts(data["receipts"])


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
