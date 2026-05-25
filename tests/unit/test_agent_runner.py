# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""Unit tests for critique_executor.agent_runner.run_agent.

subprocess.run is mocked so no real `claude` CLI is invoked, but the
command construction, JSON parsing, and failure handling are all asserted
against real behavior.
"""
from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace
from unittest.mock import patch

from critique_executor.agent_runner import run_agent


def _completed(returncode: int = 0, stdout: str = "", stderr: str = ""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def test_success_parses_result_field_from_json():
    payload = json.dumps({"result": "the answer"})
    with patch("subprocess.run", return_value=_completed(stdout=payload)) as m:
        success, output = run_agent("solve it", working_dir="/tmp", model="claude-sonnet-4-6")

    assert success is True
    assert output == "the answer"
    # command is built as a claude invocation with the goal as --message
    cmd = m.call_args.args[0]
    assert cmd[0] == "claude"
    assert "--message" in cmd
    assert cmd[cmd.index("--message") + 1] == "solve it"
    assert "--model" in cmd and cmd[cmd.index("--model") + 1] == "claude-sonnet-4-6"
    assert "--no-auto-commits" in cmd
    assert m.call_args.kwargs["cwd"] == "/tmp"


def test_non_json_stdout_returned_verbatim():
    with patch("subprocess.run", return_value=_completed(stdout="plain text")):
        success, output = run_agent("goal", working_dir=".", model="claude-sonnet-4-6")

    assert success is True
    assert output == "plain text"


def test_rejection_reason_is_appended_to_message():
    with patch("subprocess.run", return_value=_completed(stdout="ok")) as m:
        run_agent("goal", working_dir=".", model="claude-sonnet-4-6", rejection_reason="too vague")

    message = m.call_args.args[0][m.call_args.args[0].index("--message") + 1]
    assert message.startswith("goal")
    assert "too vague" in message
    assert "Please revise" in message


def test_no_rejection_reason_sends_bare_goal():
    with patch("subprocess.run", return_value=_completed(stdout="ok")) as m:
        run_agent("just the goal", working_dir=".", model="claude-sonnet-4-6")

    message = m.call_args.args[0][m.call_args.args[0].index("--message") + 1]
    assert message == "just the goal"


def test_nonzero_returncode_is_failure():
    with patch("subprocess.run", return_value=_completed(returncode=1, stderr="boom")):
        success, output = run_agent("goal", working_dir=".", model="claude-sonnet-4-6")

    assert success is False
    assert "boom" in output


def test_nonzero_returncode_prefers_stdout_over_stderr():
    with patch(
        "subprocess.run",
        return_value=_completed(returncode=2, stdout="partial", stderr="err"),
    ):
        success, output = run_agent("goal", working_dir=".", model="claude-sonnet-4-6")

    assert success is False
    assert output == "partial"


def test_timeout_returns_descriptive_failure():
    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=5),
    ):
        success, output = run_agent("goal", working_dir=".", model="claude-sonnet-4-6", timeout_seconds=5)

    assert success is False
    assert "timed out" in output
    assert "5s" in output


def test_missing_cli_returns_failure():
    with patch("subprocess.run", side_effect=FileNotFoundError):
        success, output = run_agent("goal", working_dir=".", model="claude-sonnet-4-6")

    assert success is False
    assert "claude CLI not found" in output


def test_timeout_seconds_passed_to_subprocess():
    with patch("subprocess.run", return_value=_completed(stdout="ok")) as m:
        run_agent("goal", working_dir=".", model="claude-sonnet-4-6", timeout_seconds=42)

    assert m.call_args.kwargs["timeout"] == 42


def test_claude_effort_and_system_prompt_are_forwarded():
    with patch("subprocess.run", return_value=_completed(stdout="ok")) as m:
        run_agent(
            "goal",
            working_dir=".",
            model="claude-sonnet-4-6",
            system_prompt="system",
            effort="medium",
        )

    cmd = m.call_args.args[0]
    assert "--effort" in cmd and cmd[cmd.index("--effort") + 1] == "medium"
    assert "--append-system-prompt" in cmd


def test_codex_backend_uses_backend_specific_command_shape():
    with patch("subprocess.run", return_value=_completed(stdout="codex")) as m:
        success, output = run_agent(
            "goal",
            working_dir=".",
            model="gpt-5.4",
            effort="low",
            backend="codex_cli",
        )

    assert success is True
    assert output == "codex"
    cmd = m.call_args.args[0]
    assert cmd[0] == "codex"
    assert "--model" in cmd and cmd[cmd.index("--model") + 1] == "gpt-5.4"
    assert 'model_reasoning_effort="low"' in cmd
