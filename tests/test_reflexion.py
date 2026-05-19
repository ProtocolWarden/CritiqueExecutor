# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import json
from unittest.mock import MagicMock, call, patch

from critique_executor.models import CritiqueConfig, CritiqueTopology, VerdictStatus
from critique_executor.reflexion import ReflexionLoop


def _make_config(**kwargs) -> CritiqueConfig:
    defaults = {"topology": CritiqueTopology.REFLEXION, "max_rounds": 5}
    defaults.update(kwargs)
    return CritiqueConfig(**defaults)


def _accept_response() -> MagicMock:
    msg = MagicMock()
    msg.content[0].text = json.dumps({"status": "accept", "reason": "ok"})
    return msg


def _reject_response(reason: str = "bad") -> MagicMock:
    msg = MagicMock()
    msg.content[0].text = json.dumps({"status": "reject", "reason": reason})
    return msg


def test_accept_on_round_1():
    client = MagicMock()
    client.messages.create.return_value = _accept_response()
    config = _make_config()

    with patch("critique_executor.reflexion.run_agent", return_value=(True, "output")):
        loop = ReflexionLoop(config, client)
        trace = loop.run("goal")

    assert trace.accepted is True
    assert len(trace.rounds) == 1


def test_reject_twice_then_accept():
    client = MagicMock()
    client.messages.create.side_effect = [
        _reject_response("r1"), _reject_response("r2"), _accept_response()
    ]
    config = _make_config()

    with patch("critique_executor.reflexion.run_agent", return_value=(True, "output")):
        loop = ReflexionLoop(config, client)
        trace = loop.run("goal")

    assert trace.accepted is True
    assert len(trace.rounds) == 3
    assert trace.rounds[0].verdict.status == VerdictStatus.REJECT
    assert trace.rounds[2].verdict.status == VerdictStatus.ACCEPT


def test_criteria_included_in_critic_call():
    client = MagicMock()
    client.messages.create.return_value = _accept_response()
    config = _make_config(criteria=["must be concise", "must be correct"])

    captured_calls = []
    original_run_critic = None

    def fake_critic(proposal, goal_text, criteria, critic_model, critic_system_prompt,
                    anthropic_client, round_num):
        captured_calls.append(criteria)
        from critique_executor.models import CritiqueVerdict, VerdictStatus
        return CritiqueVerdict(status=VerdictStatus.ACCEPT, reason="ok", round=round_num)

    with patch("critique_executor.reflexion.run_agent", return_value=(True, "output")):
        with patch("critique_executor.reflexion.run_critic", side_effect=fake_critic):
            loop = ReflexionLoop(config, client)
            loop.run("goal")

    assert captured_calls[0] == ["must be concise", "must be correct"]


def test_agent_receives_rejection_reason_only():
    client = MagicMock()
    client.messages.create.side_effect = [_reject_response("fix x"), _accept_response()]
    config = _make_config()

    agent_calls = []
    def fake_agent(goal_text, working_dir, system_prompt="", rejection_reason=None, timeout_seconds=3600):
        agent_calls.append({"goal_text": goal_text, "rejection_reason": rejection_reason})
        return (True, "output")

    with patch("critique_executor.reflexion.run_agent", side_effect=fake_agent):
        loop = ReflexionLoop(config, client)
        loop.run("the goal")

    assert agent_calls[0]["rejection_reason"] is None
    assert agent_calls[1]["rejection_reason"] == "fix x"
    # goal_text is always the original, not critic identity
    assert agent_calls[1]["goal_text"] == "the goal"


def test_critic_gets_fresh_context_each_round():
    """Verify run_critic is called with round_num incrementing (fresh per round)."""
    client = MagicMock()
    client.messages.create.side_effect = [_reject_response(), _accept_response()]
    config = _make_config()

    round_nums = []
    def fake_critic(proposal, goal_text, criteria, critic_model, critic_system_prompt,
                    anthropic_client, round_num):
        round_nums.append(round_num)
        from critique_executor.models import CritiqueVerdict, VerdictStatus
        status = VerdictStatus.REJECT if round_num == 1 else VerdictStatus.ACCEPT
        return CritiqueVerdict(status=status, reason="r", round=round_num)

    with patch("critique_executor.reflexion.run_agent", return_value=(True, "output")):
        with patch("critique_executor.reflexion.run_critic", side_effect=fake_critic):
            loop = ReflexionLoop(config, client)
            loop.run("goal")

    assert round_nums == [1, 2]
