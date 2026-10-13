# Arena Repair Notes: search.py

## What changed and why

### Side-by-side comparison

| Original buggy starter | Modified repair |
|---|---|
| `self.path = Path(path)` | `self.path = Path(path)` **+ `self.documents = json.loads(...)`** |
| Loads JSON **inside `search()`** on every call | Loads JSON **once in `__init__`** and stores it |
| `query in doc["text"]` — exact, case-sensitive match | `trimmed.lower()` in `doc["text"].lower()` — case-insensitive |
| No guard for empty string or bad limit | `if not trimmed or limit <= 0: return []` |
| `return matches[:limit + 1]` — off-by-one bug | `return matches[:limit]` — correct slice |

---

## The four deliberate bugs and their fixes

1. **Repeated file I/O**
   - *Bug:* The original re-read `documents.json` on every search call.
   - *Fix:* Moved the JSON load into `__init__` and cached it in `self.documents`.

2. **Case sensitivity**
   - *Bug:* The original `"password"` would **not** match a document containing `"Password"`.
   - *Fix:* Lowercased both the query and the document text before matching.

3. **No input validation**
   - *Bug:* The original accepted empty string queries and negative/zero limits. The `test_search_extra.py` test suite explicitly checks `library.search("password", limit=-1)`.
   - *Fix:* Added `query.strip()` and an early return guard: `if not trimmed or limit <= 0: return []`.

4. **Off-by-one slice**
   - *Bug:* The original `matches[:limit + 1]` returned `limit + 1` results instead of `limit`.
   - *Fix:* Changed to `matches[:limit]`.

---

## One-liner to tell a teammate

> "The starter had four deliberate bugs. I moved the JSON load into `__init__` so we aren't re-reading the file on every search, added a guard for empty queries and invalid limits, made matching case-insensitive by lowercasing both sides, and fixed the slice so `limit=1` actually returns one result instead of two."
