# Backlog

## In Progress

_(none)_

## Up Next

- [ ] Integration tests against real Anthropic API (marked `integration`)
- [ ] CxRP contract wiring (RuntimeInvocation → CritiqueExecutorRunner)
- [ ] OC registration in executor registry

## Done

- [x] Initial package scaffolding (pyproject.toml, src layout)
- [x] models.py: CritiqueVerdict, CritiqueTrace, CritiqueConfig
- [x] verdict.py: parse_verdict()
- [x] trace.py: CritiqueTraceBuilder
- [x] agent_runner.py: run_agent() subprocess wrapper
- [x] critic_runner.py: run_critic() Anthropic API wrapper
- [x] adversarial.py: AdversarialLoop
- [x] reflexion.py: ReflexionLoop
- [x] executor.py: CritiqueExecutorRunner routing to RxP RuntimeResult
- [x] Full test suite (all topologies, mocked)
- [x] Git initialized, initial commit on main
- [x] Clarified internal "draft agent" wording in docs/docstrings while
  keeping `proposer_*` config names stable
