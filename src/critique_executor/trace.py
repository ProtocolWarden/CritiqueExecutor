# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from critique_executor.models import CritiqueRound, CritiqueTopology, CritiqueTrace, CritiqueVerdict


class CritiqueTraceBuilder:
    def __init__(self, topology: CritiqueTopology, goal_text: str) -> None:
        self._topology = topology
        self._goal_text = goal_text
        self._rounds: list[CritiqueRound] = []

    def add_round(self, proposal: str, verdict: CritiqueVerdict) -> None:
        self._rounds.append(
            CritiqueRound(round_num=verdict.round, proposal=proposal, verdict=verdict)
        )

    def build(self, final_output: str | None, accepted: bool) -> CritiqueTrace:
        return CritiqueTrace(
            topology=self._topology,
            goal_text=self._goal_text,
            rounds=list(self._rounds),
            final_output=final_output,
            accepted=accepted,
        )
