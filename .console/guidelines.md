# Guidelines

_Stable repo policy for Claude. Low-churn. Not a scratchpad or task list._
_Edit when project rules change — not during normal work sessions._

## Branch Policy

- Do not commit directly to `main` or `master`.
- Before making any changes, confirm you are on a feature branch.
- If on a protected branch, stop and ask the operator to create a working branch.

## Session Start

1. Read `.console/.context` — your compiled startup context for this session.
2. Summarize your plan before making any edits.
3. Confirm you are on the correct branch.

## During Work

- Run `pytest tests/ -x -q` before and after changes.
- Keep SPDX headers on all Python files.
- No print() calls in library code.
- Line length 100.

## Invariants

- Critic isolation: critic never sees proposer system prompt (and vice versa).
- Agent receives only rejection_reason, not critic identity.
- max_rounds hard cap is 10 (enforced in CritiqueConfig.__post_init__).
- Always return RxP RuntimeResult from CritiqueExecutorRunner.run().
