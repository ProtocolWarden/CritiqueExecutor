# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from critique_executor.models import CritiqueTopology, CritiqueVerdict, VerdictStatus
from critique_executor.trace import CritiqueTraceBuilder


def test_build_with_multiple_rounds():
    builder = CritiqueTraceBuilder(CritiqueTopology.ADVERSARIAL, "goal text")
    v1 = CritiqueVerdict(status=VerdictStatus.REJECT, reason="r1", round=1)
    v2 = CritiqueVerdict(status=VerdictStatus.ACCEPT, reason="ok", round=2)
    builder.add_round("proposal 1", v1)
    builder.add_round("proposal 2", v2)
    trace = builder.build(final_output="proposal 2", accepted=True)

    assert len(trace.rounds) == 2
    assert trace.accepted is True
    assert trace.final_output == "proposal 2"
    assert trace.rounds[0].round_num == 1
    assert trace.rounds[1].round_num == 2


def test_build_empty_rounds():
    builder = CritiqueTraceBuilder(CritiqueTopology.REFLEXION, "some goal")
    trace = builder.build(final_output=None, accepted=False)

    assert len(trace.rounds) == 0
    assert trace.accepted is False
    assert trace.final_output is None
    assert trace.goal_text == "some goal"


def test_to_evidence_dict_counts_rejections():
    builder = CritiqueTraceBuilder(CritiqueTopology.REFLEXION, "goal")
    for i in range(1, 4):
        v = CritiqueVerdict(status=VerdictStatus.REJECT, reason=f"reason {i}", round=i)
        builder.add_round(f"proposal {i}", v)

    v_accept = CritiqueVerdict(status=VerdictStatus.ACCEPT, reason="done", round=4)
    builder.add_round("final proposal", v_accept)
    trace = builder.build(final_output="final proposal", accepted=True)

    evidence = trace.to_evidence_dict()
    assert evidence["total_rounds"] == 4
    assert len(evidence["rejection_reasons"]) == 3


def test_rounds_list_is_independent_copy():
    builder = CritiqueTraceBuilder(CritiqueTopology.ADVERSARIAL, "goal")
    v = CritiqueVerdict(status=VerdictStatus.ACCEPT, reason="ok", round=1)
    builder.add_round("p1", v)
    trace = builder.build("p1", True)

    # Mutating builder after build should not affect trace
    v2 = CritiqueVerdict(status=VerdictStatus.REJECT, reason="no", round=2)
    builder.add_round("p2", v2)
    assert len(trace.rounds) == 1
