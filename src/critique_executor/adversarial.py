# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from critique_executor._loop import run_critique_loop
from critique_executor.models import CritiqueConfig, CritiqueTopology, CritiqueTrace


class AdversarialLoop:
    """Draft-agent + critic loop. Neither sees the other's system prompt.

    Isolation invariant: the draft agent and critic are distinct agents and
    the draft agent never learns the critic's identity or system prompt — it
    only receives the rejection reason from the prior round.
    """

    def __init__(self, config: CritiqueConfig) -> None:
        self._config = config

    def run(self, goal_text: str) -> CritiqueTrace:
        return run_critique_loop(CritiqueTopology.ADVERSARIAL, self._config, goal_text)
