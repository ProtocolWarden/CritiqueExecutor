# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class VerdictStatus(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"


class CritiqueTopology(str, Enum):
    ADVERSARIAL = "adversarial"
    REFLEXION = "reflexion"


@dataclass
class CritiqueVerdict:
    status: VerdictStatus
    reason: str
    round: int


@dataclass
class CritiqueRound:
    round_num: int
    proposal: str
    verdict: CritiqueVerdict


@dataclass
class CritiqueTrace:
    topology: CritiqueTopology
    goal_text: str
    rounds: list[CritiqueRound]
    final_output: str | None
    accepted: bool

    def to_evidence_dict(self) -> dict[str, Any]:
        return {
            "topology": self.topology.value,
            "total_rounds": len(self.rounds),
            "accepted": self.accepted,
            "rejection_reasons": [
                r.verdict.reason for r in self.rounds
                if r.verdict.status == VerdictStatus.REJECT
            ],
        }


@dataclass
class CritiqueConfig:
    topology: CritiqueTopology
    proposer_model: str = "claude-sonnet-4-6"
    critic_model: str = "claude-sonnet-4-6"
    proposer_effort: str | None = None
    critic_effort: str | None = None
    proposer_backend_models: dict[str, str] = field(default_factory=dict)
    critic_backend_models: dict[str, str] = field(default_factory=dict)
    proposer_backend_efforts: dict[str, str] = field(default_factory=dict)
    critic_backend_efforts: dict[str, str] = field(default_factory=dict)
    max_rounds: int = 5
    criteria: list[str] = field(default_factory=list)
    proposer_system_prompt: str = ""
    critic_system_prompt: str = ""
    working_dir: str = "."
    timeout_seconds: int = 3600
    worker_backend: str = "claude_code"

    def __post_init__(self) -> None:
        if self.max_rounds > 10:
            self.max_rounds = 10

    def proposer_model_for_backend(self, backend: str) -> str:
        return self.proposer_backend_models.get(backend, self.proposer_model)

    def critic_model_for_backend(self, backend: str) -> str:
        return self.critic_backend_models.get(backend, self.critic_model)

    def proposer_effort_for_backend(self, backend: str) -> str | None:
        return self.proposer_backend_efforts.get(backend, self.proposer_effort)

    def critic_effort_for_backend(self, backend: str) -> str | None:
        return self.critic_backend_efforts.get(backend, self.critic_effort)
