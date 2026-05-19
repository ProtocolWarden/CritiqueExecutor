# Log

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
