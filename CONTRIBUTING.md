# Contributing to CritiqueExecutor

CritiqueExecutor runs adversarial (proposer+critic) and reflexion (agent+independent critic) critique loops for iterative AI task refinement. The critic always evaluates in isolation — it never sees the proposer/agent identity.

## Before You Start

- Check open issues to avoid duplicate work
- For significant changes, open an issue first to discuss the approach
- All contributions must pass the test suite and linter before merging

## Development Setup

```bash
git clone https://github.com/ProtocolWarden/CritiqueExecutor.git
cd CritiqueExecutor
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Requires Python 3.11+.

## Running Tests

```bash
.venv/bin/python -m pytest tests/ -v
```

## Invariants

- **max_rounds**: hard-capped at 10 (enforced in `CritiqueConfig.__post_init__`).
- Critic isolation: the agent/proposer identity must never reach the critic prompt.
- Topology routing: `adversarial` and `reflexion` are the only valid topologies — no fallback.
