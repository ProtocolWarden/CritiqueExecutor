# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from critique_executor._loop import run_critique_loop
from critique_executor.models import CritiqueConfig, CritiqueTopology, CritiqueTrace


class ReflexionLoop:
    """Single agent + independent critic (fresh context each critique).

    Reflexion invariant: the critic is invoked with fresh context every
    round (no accumulated history), and the agent receives only the
    rejection reason — never the critic's identity — to drive self-revision.
    """

    def __init__(self, config: CritiqueConfig) -> None:
        self._config = config

    def run(self, goal_text: str) -> CritiqueTrace:
        return run_critique_loop(CritiqueTopology.REFLEXION, self._config, goal_text)
