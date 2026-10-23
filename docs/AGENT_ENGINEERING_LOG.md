# Agent Engineering Log

Add an entry for each session. Record only synthetic/sanitized context; exclude credentials and private conversations.

## Week 1 — 2026-10-13 — Arena repair, scoping, and repo release

- Task: repair the Arena `search.py` (document search over synthetic JSON), scope my chatbot in `docs/SCOPING.md`, and push the project to my own GitHub repo.
- Tool/model used, or agent-unavailable fallback: Pi agent, model `moonshotai/kimi-k2.6`.
- What I delegated: in practice, the whole Arena task, by accident. I let the agent read the full assignment and work on it with few constraints, so it finished both the original task and the additional requirement. I had to switch to being a learner and reviewer on the fly.
- Decisions I kept as the human lead: few in the Arena, which is the gap I want to close. I chose to have the agent explain what it was doing as it worked.
- What worked: letting the agent read the whole assignment helped me understand what was required. Its explanations and code notes helped me follow the changes. The final code passes all 11 checks.
- What failed: I didn't stop the agent after the first part of the Arena, so it went on to the additional requirement and we never rotated roles or tried a second workflow. Kate didn't review my work, so there was no independent check. Separately, the Arena folder was first committed without `data/documents.json`, so all 11 tests failed with `FileNotFoundError` when run from `exercises/week1-arena/`. Fixed by adding the synthetic data file.
- How I verified it (commands, results, and commit/file references):
  - `python -m unittest -v` on the original code → 2 passed, 5 failed (expected starting state).
  - `python -m unittest -v` in `exercises/week1-arena/` after the fix → 11 passed (7 supplied + 4 in `test_search_extra.py`).
  - `git check-ignore .env` prints `.env`; `git ls-files .env` prints nothing; `.env` has never appeared in history.
  - Commits `d1eff16` (Week 1 scope and studio evidence), `71e96ed` (Arena repair notes).
- What I still do not understand: when to let the agent do what it can, and when to give it requirements to sharpen its focus.
- One change I will make to my workflow: combine Vibe with specification-first. Write the requirements and stopping points before the agent starts, so I can learn as it goes and control the pace.

shipped: https://github.com/LBXMike/Techin509
