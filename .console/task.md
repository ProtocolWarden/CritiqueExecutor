# Task

_The current live assignment. One objective at a time._
_Replace contents when the objective changes. Do not accumulate history here — that belongs in log.md._

## Objective

Initial build of CritiqueExecutor — Phase 3 of the multi-phase executor project.
Implements adversarial and reflexion critique-loop topologies.

## Context

OC dispatches tasks via CxRP/RxP contracts. CritiqueExecutor runs propose→critique loops
until accept verdict or round limit. Integrates with Claude Code (proposer) and Anthropic
API (critic).

## Definition of Done

- All source modules written and passing pytest
- RxP RuntimeResult returned from executor
- Git initialized with initial commit on main
