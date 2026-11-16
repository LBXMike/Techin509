"""Week 7 ReceiptBot feature: deterministic lookup of purchased items."""

from __future__ import annotations


def find_item(query: str, receipts: list[dict]) -> list[dict]:
    """Find items by name without changing the receipt data."""
    if not query.strip():
        return []

    needle = query.casefold()
    matches: list[dict] = []

    for receipt in receipts:
        for item in receipt["items"]:
            if needle in item["name"].casefold():
                matches.append(
                    {
                        "receipt": receipt["id"],
                        "store": receipt["store"],
                        "date": receipt["date"],
                        "item": item["name"],
                        "price": item["price"],
                    }
                )

    return matches
