# Week 1 — Arena record

Name/team: Mike Clopton & Kate
Workflows before and after rotation: Vibe the whole time. We did not rotate or switch workflows, because the agent finished the original task and the additional requirement in one run without stopping in between.
Roles before / after rotation: No rotation. Mike and Kate both used the Vibe workflow, and no one took the reviewer role: Kate did not verify Mike's work.

## Task and checks

Required behavior of `Library.search(query, limit=3)`: case-insensitive substring match, trim the query, return `[]` for blank queries, no matches, or `limit <= 0`, return at most `limit` results, keep each result's `source` and `text`, keep input-file order, and read the JSON only once when the `Library` is built.

When the checks were written: I did not write my own checks before the agent started. I let the agent read the whole assignment first, then it worked through both the original task and the additional requirement. The table below records the checks as they stand now.

| Input or condition | Expected result | Command or steps | Actual result |
|---|---|---|---|
| `"password"` | matching doc(s) with source | `python -m unittest -v` (`test_normal_query`) | pass |
| `"PASSWORD"` | same as lowercase | `test_case_insensitive` | pass |
| `"  password  "` | spaces trimmed, matches found | `test_trim_query` | pass |
| `""` / spaces only | `[]` | `test_blank_query` | pass |
| unknown word | `[]` | `test_unknown_query` | pass |
| `limit=1` | exactly 1 result | `test_result_limit` | pass |
| `limit=0` | `[]` | `test_zero_limit` | pass |
| `limit=-1` | `[]` | `test_search_extra.py` (`test_negative_limit`) | pass |
| several matches | input-file order kept | `test_preserves_order` | pass |
| any match | `source` and `text` unchanged | `test_preserve_fields` | pass |
| JSON file deleted after `Library` is built | two later searches still work | `test_survives_file_deletion` (uses a temp copy; supplied fixture untouched) | pass |

## Evidence

- Starting failures: original `search.py` gave **2 passed, 5 failed** (`test_blank_query`, `test_case_insensitive`, `test_result_limit`, `test_trim_query`, `test_zero_limit`). This matches the expected starting state in the Arena README.
- Agent request and proposed approach: I wasn't sure how to start, so I let the agent (Pi agent, model `moonshotai/kimi-k2.6`) read the whole assignment to help me understand what was required. Then I asked it to help with the assignment and explain what it was doing. I gave it few constraints and didn't tell it to stop at checkpoints before continuing.
- Changes made and why (see `exercises/week1-arena/ARENA_REPAIR_NOTES.md`):
  1. Load the JSON once in `__init__` and store it in `self.documents`, so searches don't re-read the file and still work if the file disappears.
  2. Lowercase both the query and the text so matching ignores case.
  3. `query.strip()` plus a guard `if not trimmed or limit <= 0: return []` for blank queries and zero or negative limits.
  4. Change the slice from `matches[:limit + 1]` to `matches[:limit]` to fix an off-by-one error.
- Diff review findings: no partner reviewed the diff. In my own review I noticed the code roughly doubled in length, and in `test_search_extra.py` the agent added a comment to each test explaining what it checks.
- Additional requirement and how you checked it: load once at construction, keep file order, return `[]` for a negative limit. Checked by `test_survives_file_deletion` (copy the JSON to a temp folder, build the library, delete the copy, search twice), `test_preserves_order` and `test_negative_limit`.
- Your extra test case and result: `test_search_extra.py` adds 4 checks (file deletion, order, negative limit, field preservation). All pass.
- Final test results: `python -m unittest -v` in `exercises/week1-arena/` → **11 passed, 0 failed**. `python search.py` prints `[it.md] To reset your password, use the synthetic IT portal.`
- Code/commit link: `exercises/week1-arena/` in https://github.com/LBXMike/Techin509 (commits `d1eff16`, `71e96ed`).

## Compare workflows

Use your own results and other teams' reports. Label which evidence you observed yourself.

| Workflow | Evidence source | Speed / human effort | Correctness | Code clarity | Remaining uncertainty |
|---|---|---|---|---|---|
| Vibe | Observed (our team) | Fast, with little human effort: the agent did both parts in one run, so I had to learn and review on the fly | 11/11 tests pass | Longer code (about double); each new test has a comment explaining what it checks | When to let the agent run and when to give it requirements |
| Specification-first | Not observed: no other teams were available to compare with | — | — | — | — |
| Verification-first | Not observed: no other teams were available to compare with | — | — | — | — |

Which approach would you use for your chatbot, and why?

A mix of Vibe and specification-first. Vibe helps me learn, because the agent explains its approach. Writing requirements and stopping points first lets me control the pace and check each step before the agent moves on.
