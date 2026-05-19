# Log

_Recent decisions, stop points, what changed and why._

---

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
