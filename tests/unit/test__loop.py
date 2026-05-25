# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""Unit tests for the shared critique loop, critique_executor._loop.

run_agent / run_critic are patched at the _loop module boundary so the loop's
own round mechanics — accept/reject sequencing, round limits, rejection-reason
threading, agent-failure handling, and backend pass-through — are asserted
directly, independent of either topology wrapper.
"""
from __future__ import annotations

from unittest.mock import patch

from critique_executor._loop import run_critique_loop
from critique_executor.models import (
    CritiqueConfig,
    CritiqueTopology,
    CritiqueVerdict,
    VerdictStatus,
)


def _config(**kwargs) -> CritiqueConfig:
    defaults = {"topology": CritiqueTopology.ADVERSARIAL, "max_rounds": 5}
    defaults.update(kwargs)
    return CritiqueConfig(**defaults)


def _accept(round_num: int = 1) -> CritiqueVerdict:
    return CritiqueVerdict(status=VerdictStatus.ACCEPT, reason="ok", round=round_num)


def _reject(reason: str = "no", round_num: int = 1) -> CritiqueVerdict:
    return CritiqueVerdict(status=VerdictStatus.REJECT, reason=reason, round=round_num)


def test_accept_first_round_stops_loop():
    with (
        patch("critique_executor._loop.run_agent", return_value=(True, "prop")),
        patch("critique_executor._loop.run_critic", return_value=_accept(1)),
    ):
        trace = run_critique_loop(CritiqueTopology.REFLEXION, _config(), "goal")

    assert trace.accepted is True
    assert trace.final_output == "prop"
    assert len(trace.rounds) == 1
    # topology argument is propagated onto the trace
    assert trace.topology == CritiqueTopology.REFLEXION


def test_round_limit_without_accept():
    with (
        patch("critique_executor._loop.run_agent", return_value=(True, "p")),
        patch(
            "critique_executor._loop.run_critic",
            side_effect=[_reject(round_num=i) for i in range(1, 4)],
        ),
    ):
        trace = run_critique_loop(CritiqueTopology.ADVERSARIAL, _config(max_rounds=3), "g")

    assert trace.accepted is False
    assert trace.final_output is None
    assert len(trace.rounds) == 3


def test_rejection_reason_threaded_into_next_agent_call():
    seen: list = []

    def fake_agent(
        goal_text,
        working_dir,
        model,
        system_prompt="",
        rejection_reason=None,
        timeout_seconds=3600,
        effort=None,
        backend="claude_code",
    ):
        seen.append(rejection_reason)
        return (True, "p")

    with (
        patch("critique_executor._loop.run_agent", side_effect=fake_agent),
        patch(
            "critique_executor._loop.run_critic",
            side_effect=[_reject("fix it", 1), _accept(2)],
        ),
    ):
        run_critique_loop(CritiqueTopology.ADVERSARIAL, _config(), "g")

    assert seen == [None, "fix it"]


def test_agent_failure_records_reject_and_continues():
    with patch("critique_executor._loop.run_agent", return_value=(False, "explode")):
        trace = run_critique_loop(CritiqueTopology.ADVERSARIAL, _config(max_rounds=2), "g")

    assert trace.accepted is False
    assert len(trace.rounds) == 2
    assert all(r.verdict.status == VerdictStatus.REJECT for r in trace.rounds)
    assert "explode" in trace.rounds[0].verdict.reason


def test_agent_failure_reason_threaded_as_rejection():
    seen: list = []

    def fake_agent(
        goal_text,
        working_dir,
        model,
        system_prompt="",
        rejection_reason=None,
        timeout_seconds=3600,
        effort=None,
        backend="claude_code",
    ):
        seen.append(rejection_reason)
        return (False, "boom")

    with patch("critique_executor._loop.run_agent", side_effect=fake_agent):
        run_critique_loop(CritiqueTopology.ADVERSARIAL, _config(max_rounds=2), "g")

    assert seen[0] is None
    assert seen[1] is not None and "boom" in seen[1]


def test_worker_backend_passed_to_critic():
    captured: list = []

    def fake_critic(**kwargs):
        captured.append(kwargs)
        return _accept(1)

    with (
        patch("critique_executor._loop.run_agent", return_value=(True, "p")),
        patch("critique_executor._loop.run_critic", side_effect=fake_critic),
    ):
        run_critique_loop(
            CritiqueTopology.ADVERSARIAL,
            _config(
                worker_backend="codex_cli",
                critic_backend_models={"codex_cli": "gpt-5.4-mini"},
                critic_backend_efforts={"codex_cli": "low"},
            ),
            "g",
        )

    assert captured[0]["backend"] == "codex_cli"
    assert captured[0]["critic_model"] == "gpt-5.4-mini"
    assert captured[0]["effort"] == "low"
