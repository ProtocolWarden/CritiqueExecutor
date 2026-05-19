# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from unittest.mock import patch

from critique_executor.adversarial import AdversarialLoop
from critique_executor.models import CritiqueConfig, CritiqueTopology, CritiqueVerdict, VerdictStatus


def _make_config(**kwargs) -> CritiqueConfig:
    defaults = {"topology": CritiqueTopology.ADVERSARIAL, "max_rounds": 5}
    defaults.update(kwargs)
    return CritiqueConfig(**defaults)


def _accept_verdict(round_num: int = 1) -> CritiqueVerdict:
    return CritiqueVerdict(status=VerdictStatus.ACCEPT, reason="good", round=round_num)


def _reject_verdict(reason: str = "not good", round_num: int = 1) -> CritiqueVerdict:
    return CritiqueVerdict(status=VerdictStatus.REJECT, reason=reason, round=round_num)


def test_accept_on_round_1():
    config = _make_config()
    with (
        patch("critique_executor.adversarial.run_agent", return_value=(True, "proposal text")),
        patch("critique_executor.adversarial.run_critic", return_value=_accept_verdict(1)),
    ):
        loop = AdversarialLoop(config)
        trace = loop.run("do something")

    assert trace.accepted is True
    assert len(trace.rounds) == 1
    assert trace.final_output == "proposal text"
    assert trace.rounds[0].verdict.status == VerdictStatus.ACCEPT


def test_reject_then_accept():
    config = _make_config()
    with (
        patch("critique_executor.adversarial.run_agent", return_value=(True, "proposal")),
        patch(
            "critique_executor.adversarial.run_critic",
            side_effect=[_reject_verdict("too short", 1), _accept_verdict(2)],
        ),
    ):
        loop = AdversarialLoop(config)
        trace = loop.run("goal")

    assert trace.accepted is True
    assert len(trace.rounds) == 2
    assert trace.rounds[0].verdict.status == VerdictStatus.REJECT
    assert trace.rounds[1].verdict.status == VerdictStatus.ACCEPT


def test_max_rounds_exceeded_not_accepted():
    config = _make_config(max_rounds=3)
    with (
        patch("critique_executor.adversarial.run_agent", return_value=(True, "proposal")),
        patch(
            "critique_executor.adversarial.run_critic",
            side_effect=[_reject_verdict(round_num=i) for i in range(1, 4)],
        ),
    ):
        loop = AdversarialLoop(config)
        trace = loop.run("goal")

    assert trace.accepted is False
    assert len(trace.rounds) == 3
    assert trace.final_output is None


def test_trace_has_all_rounds():
    config = _make_config(max_rounds=5)
    with (
        patch("critique_executor.adversarial.run_agent", return_value=(True, "p")),
        patch(
            "critique_executor.adversarial.run_critic",
            side_effect=[
                _reject_verdict("r1", 1),
                _reject_verdict("r2", 2),
                _accept_verdict(3),
            ],
        ),
    ):
        loop = AdversarialLoop(config)
        trace = loop.run("goal")

    assert len(trace.rounds) == 3
    assert [r.verdict.round for r in trace.rounds] == [1, 2, 3]


def test_rejection_reason_passed_to_next_agent_call():
    config = _make_config()
    calls: list = []

    def fake_agent(goal_text, working_dir, system_prompt="", rejection_reason=None, timeout_seconds=3600):
        calls.append(rejection_reason)
        return (True, "proposal")

    with (
        patch("critique_executor.adversarial.run_agent", side_effect=fake_agent),
        patch(
            "critique_executor.adversarial.run_critic",
            side_effect=[_reject_verdict("needs more detail", 1), _accept_verdict(2)],
        ),
    ):
        loop = AdversarialLoop(config)
        loop.run("goal")

    assert calls[0] is None
    assert calls[1] == "needs more detail"


def test_run_critic_receives_worker_backend():
    config = _make_config(worker_backend="codex_cli")
    critic_calls: list = []

    def fake_critic(**kwargs):
        critic_calls.append(kwargs)
        return _accept_verdict(1)

    with (
        patch("critique_executor.adversarial.run_agent", return_value=(True, "proposal")),
        patch("critique_executor.adversarial.run_critic", side_effect=fake_critic),
    ):
        loop = AdversarialLoop(config)
        loop.run("goal")

    assert critic_calls[0]["backend"] == "codex_cli"


def test_agent_failure_counts_as_reject():
    config = _make_config(max_rounds=2)
    with (
        patch("critique_executor.adversarial.run_agent", return_value=(False, "error msg")),
    ):
        loop = AdversarialLoop(config)
        trace = loop.run("goal")

    assert trace.accepted is False
    assert all(r.verdict.status == VerdictStatus.REJECT for r in trace.rounds)
