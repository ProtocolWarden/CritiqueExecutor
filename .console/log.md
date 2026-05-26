# Log

## 2026-05-23 — Clear Custodian findings + add real unit tests

Took CritiqueExecutor from 16 Custodian findings to 0 clean.

- T1/T6/T7: wrote real unit tests under `tests/unit/` — `test_agent_runner.py`
  (run_agent: command build, JSON parse, timeout/missing-CLI, rejection-reason
  threading), `test_critic_runner.py` (run_critic: claude/codex backends,
  prompt content, verdict parsing, fallbacks), and `test__loop.py` (shared
  loop mechanics). subprocess/`safe_run` mocked; real behavior asserted.
- D11: extracted the duplicated proposer→critic loop body from
  adversarial.py/reflexion.py into `critique_executor._loop.run_critique_loop`;
  topology classes now delegate. Existing loop tests repointed to patch
  `_loop.run_agent`/`run_critic`.
- S4: added venv guard to `tests/conftest.py` (CI-skipped).
- W6: added `.hooks/pre-commit` (log.md enforcement).
- W7: rewrote `.gitignore` to the `.console/*` + `CLAUDE.md` policy.
- R3/R4/DC4: expanded README (what-it-is / is-not, quick start, architecture).
- M1: added CHANGELOG.md.
- Enabled `core.hooksPath .hooks`. 65 tests pass; audit clean.

## 2026-05-21 — Add closing fence to console-context block

Added <!-- /console-context --> end marker so OperatorConsole only replaces its
managed block and leaves repo-owned content below it untouched.

_Recent decisions, stop points, what changed and why._

---

## 2026-05-19 — Add __pycache__ / *.pyc to .gitignore; untrack bytecode

Bytecode was accidentally tracked. Added to .gitignore and removed from index.

## 2026-05-19 — ADR 0006 Phase 2: wire safe_run() in critic_runner.py

- Replaced subprocess.run() in _claude_critic() and _codex_critic() with core_runner.process.safe_run().
- Removed subprocess import; timed_out check replaces TimeoutExpired catch.
- FileNotFoundError still caught at call site (safe_run lets it propagate from Popen).
- Added core-runner dep to pyproject.toml; conftest.py adds ExecutorRuntime/src to sys.path.
- Added RuntimeInvocation + ArtifactDescriptor to rxp.contracts stub (needed by core_runner __init__).
- 40 tests pass.

## 2026-05-18 — Initial build

Built complete CritiqueExecutor package from scratch (Phase 3).

Key decisions:
- `src/` layout for clean install isolation
- `CritiqueConfig.__post_init__` enforces `max_rounds <= 10` hard cap
- Critic isolation invariant: `run_critic` receives no proposer identity;
  `run_agent` receives no critic identity — only `rejection_reason`
- `CritiqueTraceBuilder.build()` returns a copy of rounds so builder mutations
  after build don't affect returned trace
- `CritiqueExecutorRunner` catches all exceptions and returns `failed` status
  rather than propagating — callers always get a RuntimeResult
- Reflexion and adversarial share the same loop structure; the distinction is
  semantic (single-agent revision intent vs. two-party adversarial)
- conftest.py stubs rxp, cxrp, anthropic so tests run without pip installs


## 2026-05-22 — P5: Revert to CL shim (manifest-cognition work order)

Per PlatformDeployment/docs/architecture/adr/0002-work-order-manifest-cognition.md Phase 5:

- Deleted `.context/` (config.yaml + templates/) — cognition now hosted by anchoring manifest.
- Replaced `.claude/hooks/pre_tool_use.sh` (~330 lines) and `.claude/hooks/stop.sh` (~116 lines) with thin ~10-line shims that exec `cl hook <event>`. Logic lives in the CL package.
- Updated CLAUDE.md "Cognition Lifecycle" section to reflect library-consumer posture; sessions must `eval $(cl session start <manifest>)` before tools fire, else hooks fail closed.
- Cleaned `.gitignore` of stale `.context/*` rules.
- Confirmed zero CL imports in src/ (executor never coupled to CL Python API).

Branch: feat/p5-revert-to-shim. Staged, not committed.

## 2026-05-23 — Standardize pre-push hook (file only)

- Updated `.hooks/pre-push` to the auto-discovering variant. NOT activating core.hooksPath yet: repo has pre-existing audit findings that would block pushes under the fail-closed guard; activate after that cleanup.

## 2026-05-25 — Add backend-aware proposer and critic runtime tiers

- Extended `CritiqueConfig` with backend-specific proposer/critic model and effort mappings.
- `run_agent` now supports both Claude and Codex command shapes with explicit model/effort.
- `run_critic` now forwards effort for both backends.
- Shared loop now resolves proposer/critic runtime from config per backend instead of assuming one Claude-only path. Focused CritiqueExecutor test slices passed.

## 2026-05-25 — Clarify internal draft-agent wording

- Updated README, contributing/security docs, and core loop docstrings to use
  "draft agent" in human-facing prose instead of bare "proposer".
- Kept `proposer_*` config field names unchanged for compatibility.
- Added one OC adapter note so the backend-facing `proposer_*` fields are not
  confused with OC's board-facing proposer subsystem.
