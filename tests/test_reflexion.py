# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from unittest.mock import patch

from critique_executor.models import CritiqueConfig, CritiqueTopology, CritiqueVerdict, VerdictStatus
from critique_executor.reflexion import ReflexionLoop


def _make_config(**kwargs) -> CritiqueConfig:
    defaults = {"topology": CritiqueTopology.REFLEXION, "max_rounds": 5}
    defaults.update(kwargs)
    return CritiqueConfig(**defaults)


def _accept_verdict(round_num: int = 1) -> CritiqueVerdict:
    return CritiqueVerdict(status=VerdictStatus.ACCEPT, reason="ok", round=round_num)


def _reject_verdict(reason: str = "bad", round_num: int = 1) -> CritiqueVerdict:
    return CritiqueVerdict(status=VerdictStatus.REJECT, reason=reason, round=round_num)


def test_accept_on_round_1():
    config = _make_config()
    with (
        patch("critique_executor.reflexion.run_agent", return_value=(True, "output")),
        patch("critique_executor.reflexion.run_critic", return_value=_accept_verdict(1)),
    ):
        loop = ReflexionLoop(config)
        trace = loop.run("goal")

    assert trace.accepted is True
    assert len(trace.rounds) == 1


def test_reject_twice_then_accept():
    config = _make_config()
    with (
        patch("critique_executor.reflexion.run_agent", return_value=(True, "output")),
        patch(
            "critique_executor.reflexion.run_critic",
            side_effect=[_reject_verdict("r1", 1), _reject_verdict("r2", 2), _accept_verdict(3)],
        ),
    ):
        loop = ReflexionLoop(config)
        trace = loop.run("goal")

    assert trace.accepted is True
    assert len(trace.rounds) == 3
    assert trace.rounds[0].verdict.status == VerdictStatus.REJECT
    assert trace.rounds[2].verdict.status == VerdictStatus.ACCEPT


def test_criteria_included_in_critic_call():
    config = _make_config(criteria=["must be concise", "must be correct"])
    captured_calls: list = []

    def fake_critic(**kwargs):
        captured_calls.append(kwargs["criteria"])
        return _accept_verdict(kwargs["round_num"])

    with (
        patch("critique_executor.reflexion.run_agent", return_value=(True, "output")),
        patch("critique_executor.reflexion.run_critic", side_effect=fake_critic),
    ):
        loop = ReflexionLoop(config)
        loop.run("goal")

    assert captured_calls[0] == ["must be concise", "must be correct"]


def test_agent_receives_rejection_reason_only():
    config = _make_config()
    agent_calls: list = []

    def fake_agent(goal_text, working_dir, system_prompt="", rejection_reason=None, timeout_seconds=3600):
        agent_calls.append({"goal_text": goal_text, "rejection_reason": rejection_reason})
        return (True, "output")

    with (
        patch("critique_executor.reflexion.run_agent", side_effect=fake_agent),
        patch(
            "critique_executor.reflexion.run_critic",
            side_effect=[_reject_verdict("fix x", 1), _accept_verdict(2)],
        ),
    ):
        loop = ReflexionLoop(config)
        loop.run("the goal")

    assert agent_calls[0]["rejection_reason"] is None
    assert agent_calls[1]["rejection_reason"] == "fix x"
    assert agent_calls[1]["goal_text"] == "the goal"


def test_critic_gets_fresh_round_nums():
    config = _make_config()
    round_nums: list = []

    def fake_critic(**kwargs):
        round_nums.append(kwargs["round_num"])
        status = VerdictStatus.REJECT if kwargs["round_num"] == 1 else VerdictStatus.ACCEPT
        return CritiqueVerdict(status=status, reason="r", round=kwargs["round_num"])

    with (
        patch("critique_executor.reflexion.run_agent", return_value=(True, "output")),
        patch("critique_executor.reflexion.run_critic", side_effect=fake_critic),
    ):
        loop = ReflexionLoop(config)
        loop.run("goal")

    assert round_nums == [1, 2]


def test_run_critic_receives_worker_backend():
    config = _make_config(worker_backend="codex_cli")
    critic_calls: list = []

    def fake_critic(**kwargs):
        critic_calls.append(kwargs)
        return _accept_verdict(1)

    with (
        patch("critique_executor.reflexion.run_agent", return_value=(True, "output")),
        patch("critique_executor.reflexion.run_critic", side_effect=fake_critic),
    ):
        loop = ReflexionLoop(config)
        loop.run("goal")

    assert critic_calls[0]["backend"] == "codex_cli"
