# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import pytest

from critique_executor.models import (
    CritiqueConfig,
    CritiqueRound,
    CritiqueTopology,
    CritiqueTrace,
    CritiqueVerdict,
    VerdictStatus,
)


def test_verdict_status_enum_values():
    assert VerdictStatus.ACCEPT == "accept"
    assert VerdictStatus.REJECT == "reject"


def test_critique_config_hard_cap_enforced():
    config = CritiqueConfig(topology=CritiqueTopology.ADVERSARIAL, max_rounds=15)
    assert config.max_rounds == 10


def test_critique_config_below_cap_unchanged():
    config = CritiqueConfig(topology=CritiqueTopology.REFLEXION, max_rounds=3)
    assert config.max_rounds == 3


def test_critique_config_at_cap_unchanged():
    config = CritiqueConfig(topology=CritiqueTopology.ADVERSARIAL, max_rounds=10)
    assert config.max_rounds == 10


def test_critique_trace_to_evidence_dict_counts():
    reject_verdict = CritiqueVerdict(status=VerdictStatus.REJECT, reason="too vague", round=1)
    accept_verdict = CritiqueVerdict(status=VerdictStatus.ACCEPT, reason="good", round=2)
    rounds = [
        CritiqueRound(round_num=1, proposal="draft 1", verdict=reject_verdict),
        CritiqueRound(round_num=2, proposal="draft 2", verdict=accept_verdict),
    ]
    trace = CritiqueTrace(
        topology=CritiqueTopology.ADVERSARIAL,
        goal_text="do the thing",
        rounds=rounds,
        final_output="draft 2",
        accepted=True,
    )
    evidence = trace.to_evidence_dict()
    assert evidence["topology"] == "adversarial"
    assert evidence["total_rounds"] == 2
    assert evidence["accepted"] is True
    assert evidence["rejection_reasons"] == ["too vague"]


def test_critique_trace_to_evidence_dict_all_rejected():
    verdicts = [
        CritiqueVerdict(status=VerdictStatus.REJECT, reason=f"reason {i}", round=i)
        for i in range(1, 4)
    ]
    rounds = [CritiqueRound(round_num=v.round, proposal=f"p{v.round}", verdict=v) for v in verdicts]
    trace = CritiqueTrace(
        topology=CritiqueTopology.REFLEXION,
        goal_text="goal",
        rounds=rounds,
        final_output=None,
        accepted=False,
    )
    evidence = trace.to_evidence_dict()
    assert evidence["accepted"] is False
    assert len(evidence["rejection_reasons"]) == 3
