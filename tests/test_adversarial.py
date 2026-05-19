# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from critique_executor.adversarial import AdversarialLoop
from critique_executor.models import CritiqueConfig, CritiqueTopology, VerdictStatus


def _make_config(**kwargs) -> CritiqueConfig:
    defaults = {"topology": CritiqueTopology.ADVERSARIAL, "max_rounds": 5}
    defaults.update(kwargs)
    return CritiqueConfig(**defaults)


def _accept_response() -> MagicMock:
    msg = MagicMock()
    msg.content[0].text = json.dumps({"status": "accept", "reason": "good"})
    return msg


def _reject_response(reason: str = "not good") -> MagicMock:
    msg = MagicMock()
    msg.content[0].text = json.dumps({"status": "reject", "reason": reason})
    return msg


def test_accept_on_round_1():
    client = MagicMock()
    client.messages.create.return_value = _accept_response()
    config = _make_config()

    with patch("critique_executor.adversarial.run_agent", return_value=(True, "proposal text")):
        loop = AdversarialLoop(config, client)
        trace = loop.run("do something")

    assert trace.accepted is True
    assert len(trace.rounds) == 1
    assert trace.final_output == "proposal text"
    assert trace.rounds[0].verdict.status == VerdictStatus.ACCEPT


def test_reject_then_accept():
    client = MagicMock()
    client.messages.create.side_effect = [_reject_response("too short"), _accept_response()]
    config = _make_config()

    with patch("critique_executor.adversarial.run_agent", return_value=(True, "proposal")):
        loop = AdversarialLoop(config, client)
        trace = loop.run("goal")

    assert trace.accepted is True
    assert len(trace.rounds) == 2
    assert trace.rounds[0].verdict.status == VerdictStatus.REJECT
    assert trace.rounds[1].verdict.status == VerdictStatus.ACCEPT


def test_max_rounds_exceeded_not_accepted():
    client = MagicMock()
    client.messages.create.return_value = _reject_response("always wrong")
    config = _make_config(max_rounds=3)

    with patch("critique_executor.adversarial.run_agent", return_value=(True, "proposal")):
        loop = AdversarialLoop(config, client)
        trace = loop.run("goal")

    assert trace.accepted is False
    assert len(trace.rounds) == 3
    assert trace.final_output is None


def test_trace_has_all_rounds():
    client = MagicMock()
    client.messages.create.side_effect = [
        _reject_response("r1"),
        _reject_response("r2"),
        _accept_response(),
    ]
    config = _make_config(max_rounds=5)

    with patch("critique_executor.adversarial.run_agent", return_value=(True, "p")):
        loop = AdversarialLoop(config, client)
        trace = loop.run("goal")

    assert len(trace.rounds) == 3
    assert [r.verdict.round for r in trace.rounds] == [1, 2, 3]


def test_rejection_reason_passed_to_next_agent_call():
    client = MagicMock()
    client.messages.create.side_effect = [_reject_response("needs more detail"), _accept_response()]
    config = _make_config()

    calls = []
    def fake_agent(goal_text, working_dir, system_prompt="", rejection_reason=None, timeout_seconds=3600):
        calls.append(rejection_reason)
        return (True, "proposal")

    with patch("critique_executor.adversarial.run_agent", side_effect=fake_agent):
        loop = AdversarialLoop(config, client)
        loop.run("goal")

    assert calls[0] is None
    assert calls[1] == "needs more detail"
