# CritiqueExecutor

Critique-loop execution backend implementing **adversarial** and **reflexion**
topologies. Runs propose→critique rounds until an accept verdict or the round
limit is reached, and reports the outcome as an RxP `RuntimeResult`.

## What this repo is

- A thin **execution-backend shim**: it drives an internal draft agent (a CLI
  subprocess) and an independent critic (`claude` or `codex` CLI), looping
  until the critic returns an `accept` verdict or `max_rounds` is hit.
- The single entry point is `CritiqueExecutorRunner` (`src/critique_executor/executor.py`),
  which picks `AdversarialLoop` or `ReflexionLoop` and returns an
  `rxp.contracts.RuntimeResult` summarizing the run.
- Process execution is delegated to `core_runner.process.safe_run` for the
  critic; verdicts are parsed from `{"status": ..., "reason": ...}` JSON.

## What this repo is not

- It is **not an orchestrator or scheduler**. It executes a single critique
  loop when dispatched; it does not decide *which* goals to run or sequence
  multiple tasks.
- It is **not an LLM client library**. It shells out to CLI tools rather than
  calling provider HTTP APIs directly.
- It does **not host its own cognition**. Per the platform cognition
  lifecycle, sessions are anchored by a manifest repo; this repo carries only a
  `.console/` operational workspace and thin hook shims.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest -q          # or: .venv/bin/pytest -q
```

Programmatic use:

```python
from critique_executor import CritiqueExecutorRunner

runner = CritiqueExecutorRunner("adversarial", worker_backend="claude_code")
result = runner.run(
    "Implement a binary search function",
    max_rounds=3,
    criteria=["handles empty input", "O(log n)"],
)
print(result.status)   # "succeeded" | "rejected" | "failed"
```

## Architecture

```
CritiqueExecutorRunner            (executor.py — entry point, RxP result)
        │  selects topology
        ▼
AdversarialLoop / ReflexionLoop   (adversarial.py / reflexion.py)
        │  delegate to shared loop
        ▼
run_critique_loop                 (_loop.py — round mechanics)
        ├── run_agent             (agent_runner.py — draft agent via CLI)
        ├── run_critic            (critic_runner.py — critic via `claude`/`codex`)
        │        └── parse_verdict (verdict.py)
        └── CritiqueTraceBuilder  (trace.py → CritiqueTrace, models.py)
```

Key invariants:

- **Isolation**: the draft agent never sees the critic's identity or system
  prompt; it receives only the prior round's rejection reason.
- **Compatibility**: config fields still use the historical `proposer_*`
  names, but those fields refer to the internal draft-producing agent inside
  CritiqueExecutor, not OC's board-facing proposer lane.
- **Fresh critic context** each round (reflexion); criteria are passed
  explicitly in the prompt.
- The shared round mechanics live once in `_loop.py`; the topology classes
  only declare their topology and document their boundary invariants.

## Development

```bash
.venv/bin/pytest -q
```

Tests live under `tests/` (loop behavior) and `tests/unit/` (runner units).
A pre-commit hook requires `.console/log.md` to be updated alongside source
changes; enable hooks with `git config core.hooksPath .hooks`.

## License

Apache-2.0
