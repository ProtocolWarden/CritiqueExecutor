# CritiqueExecutor

Critique-loop executor implementing adversarial and reflexion topologies.

Dispatched by OperationsCenter via CxRP/RxP contracts. Runs propose→critique loops
until an accept verdict or round limit is reached.

## Topologies

- **adversarial**: Separate proposer (Claude Code subprocess) and critic (Anthropic API).
  Neither sees the other's system prompt. Proposer receives only the rejection reason.
- **reflexion**: Same loop structure, but intended for a single agent doing self-revision
  guided by an independent critic. Critic uses declared criteria from config.

## Usage

```python
from critique_executor import CritiqueExecutorRunner

runner = CritiqueExecutorRunner("adversarial", api_key="sk-...")
result = runner.run("Implement a binary search function", max_rounds=3)
print(result.status)   # "succeeded" | "rejected" | "failed"
```

## Development

```bash
python -m pip install -e ".[dev]"
pytest tests/ -x -q
```

## License

Apache-2.0
