# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""Unit tests for critique_executor.critic_runner.run_critic.

core_runner.process.safe_run is patched so no real CLI is spawned, but the
prompt construction, backend selection, JSON parsing, and timeout/missing-CLI
fallbacks are asserted against real behavior.
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

from critique_executor.critic_runner import run_critic
from critique_executor.models import VerdictStatus


def _result(stdout: str = "", stderr: str = "", timed_out: bool = False):
    return SimpleNamespace(stdout=stdout, stderr=stderr, timed_out=timed_out)


def _verdict_json(status: str, reason: str) -> str:
    return json.dumps({"result": json.dumps({"status": status, "reason": reason})})


def test_claude_backend_accept_verdict():
    with patch(
        "critique_executor.critic_runner.safe_run",
        return_value=_result(stdout=_verdict_json("accept", "looks good")),
    ) as m:
        verdict = run_critic(
            proposal="some code",
            goal_text="write a function",
            criteria=["correct", "tested"],
            critic_model="claude-x",
            critic_system_prompt="be strict",
            round_num=3,
        )

    assert verdict.status == VerdictStatus.ACCEPT
    assert verdict.reason == "looks good"
    assert verdict.round == 3
    cmd = m.call_args.args[0]
    assert cmd[0] == "claude"
    assert "--append-system-prompt" in cmd
    assert "--model" in cmd and cmd[cmd.index("--model") + 1] == "claude-x"


def test_claude_backend_reject_verdict():
    with patch(
        "critique_executor.critic_runner.safe_run",
        return_value=_result(stdout=_verdict_json("reject", "incomplete")),
    ):
        verdict = run_critic(
            proposal="p", goal_text="g", criteria=[], critic_model="m",
            critic_system_prompt="", round_num=1,
        )

    assert verdict.status == VerdictStatus.REJECT
    assert verdict.reason == "incomplete"


def test_prompt_includes_goal_proposal_and_criteria():
    with patch("critique_executor.critic_runner.safe_run", return_value=_result(
        stdout=_verdict_json("accept", "ok"))) as m:
        run_critic(
            proposal="PROPOSAL_BODY", goal_text="THE_GOAL",
            criteria=["crit-one", "crit-two"], critic_model="m",
            critic_system_prompt="", round_num=1,
        )

    cmd = m.call_args.args[0]
    prompt = cmd[cmd.index("--message") + 1]
    assert "THE_GOAL" in prompt
    assert "PROPOSAL_BODY" in prompt
    assert "- crit-one" in prompt
    assert "- crit-two" in prompt


def test_empty_criteria_renders_placeholder():
    with patch("critique_executor.critic_runner.safe_run", return_value=_result(
        stdout=_verdict_json("accept", "ok"))) as m:
        run_critic(
            proposal="p", goal_text="g", criteria=[], critic_model="m",
            critic_system_prompt="", round_num=1,
        )

    prompt = m.call_args.args[0][m.call_args.args[0].index("--message") + 1]
    assert "(none specified)" in prompt


def test_no_system_prompt_omits_append_flag():
    with patch("critique_executor.critic_runner.safe_run", return_value=_result(
        stdout=_verdict_json("accept", "ok"))) as m:
        run_critic(
            proposal="p", goal_text="g", criteria=[], critic_model="m",
            critic_system_prompt="", round_num=1,
        )

    assert "--append-system-prompt" not in m.call_args.args[0]


def test_codex_backend_uses_codex_command_and_raw_stdout():
    with patch(
        "critique_executor.critic_runner.safe_run",
        return_value=_result(stdout='{"status": "accept", "reason": "fine"}'),
    ) as m:
        verdict = run_critic(
            proposal="p", goal_text="g", criteria=[], critic_model="o4",
            critic_system_prompt="", round_num=2, backend="codex_cli",
        )

    assert m.call_args.args[0][0] == "codex"
    assert "--model" in m.call_args.args[0]
    assert verdict.status == VerdictStatus.ACCEPT
    assert verdict.reason == "fine"


def test_effort_forwarded_to_both_backends():
    with patch(
        "critique_executor.critic_runner.safe_run",
        return_value=_result(stdout=_verdict_json("accept", "ok")),
    ) as m:
        run_critic(
            proposal="p", goal_text="g", criteria=[], critic_model="m",
            critic_system_prompt="", round_num=1, effort="medium",
        )
    assert "--effort" in m.call_args.args[0]
    assert "medium" in m.call_args.args[0]

    with patch(
        "critique_executor.critic_runner.safe_run",
        return_value=_result(stdout='{"status": "accept", "reason": "ok"}'),
    ) as m:
        run_critic(
            proposal="p", goal_text="g", criteria=[], critic_model="gpt-5.4",
            critic_system_prompt="", round_num=1, effort="low", backend="codex_cli",
        )
    assert 'model_reasoning_effort="low"' in m.call_args.args[0]


def test_claude_timeout_yields_reject_verdict():
    with patch(
        "critique_executor.critic_runner.safe_run",
        return_value=_result(timed_out=True),
    ):
        verdict = run_critic(
            proposal="p", goal_text="g", criteria=[], critic_model="m",
            critic_system_prompt="", round_num=4,
        )

    assert verdict.status == VerdictStatus.REJECT
    assert "timed out" in verdict.reason
    assert verdict.round == 4


def test_claude_missing_cli_yields_reject_verdict():
    with patch(
        "critique_executor.critic_runner.safe_run",
        side_effect=FileNotFoundError,
    ):
        verdict = run_critic(
            proposal="p", goal_text="g", criteria=[], critic_model="m",
            critic_system_prompt="", round_num=1,
        )

    assert verdict.status == VerdictStatus.REJECT
    assert "claude CLI not found" in verdict.reason


def test_codex_missing_cli_yields_reject_verdict():
    with patch(
        "critique_executor.critic_runner.safe_run",
        side_effect=FileNotFoundError,
    ):
        verdict = run_critic(
            proposal="p", goal_text="g", criteria=[], critic_model="m",
            critic_system_prompt="", round_num=1, backend="codex_cli",
        )

    assert verdict.status == VerdictStatus.REJECT
    assert "codex CLI not found" in verdict.reason


def test_unparseable_response_falls_back_to_reject():
    with patch(
        "critique_executor.critic_runner.safe_run",
        return_value=_result(stdout="not json at all"),
    ):
        verdict = run_critic(
            proposal="p", goal_text="g", criteria=[], critic_model="m",
            critic_system_prompt="", round_num=1,
        )

    assert verdict.status == VerdictStatus.REJECT
    assert "not json at all" in verdict.reason
