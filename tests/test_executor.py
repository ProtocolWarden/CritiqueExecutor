# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from critique_executor.executor import CritiqueExecutorRunner
from critique_executor.models import CritiqueConfig, CritiqueTopology, CritiqueTrace, VerdictStatus


def _make_accepted_trace(topology: CritiqueTopology) -> CritiqueTrace:
    from critique_executor.models import CritiqueRound, CritiqueVerdict
    verdict = CritiqueVerdict(status=VerdictStatus.ACCEPT, reason="ok", round=1)
    return CritiqueTrace(
        topology=topology,
        goal_text="goal",
        rounds=[CritiqueRound(round_num=1, proposal="output", verdict=verdict)],
        final_output="output",
        accepted=True,
    )


def _make_rejected_trace(topology: CritiqueTopology) -> CritiqueTrace:
    from critique_executor.models import CritiqueRound, CritiqueVerdict
    verdict = CritiqueVerdict(status=VerdictStatus.REJECT, reason="bad", round=1)
    return CritiqueTrace(
        topology=topology,
        goal_text="goal",
        rounds=[CritiqueRound(round_num=1, proposal="output", verdict=verdict)],
        final_output=None,
        accepted=False,
    )


def test_routes_to_adversarial():
    with patch("critique_executor.executor.AdversarialLoop") as mock_loop_cls:
        mock_loop = MagicMock()
        mock_loop.run.return_value = _make_accepted_trace(CritiqueTopology.ADVERSARIAL)
        mock_loop_cls.return_value = mock_loop

        runner = CritiqueExecutorRunner("adversarial")
        result = runner.run("do something")

    mock_loop_cls.assert_called_once()
    mock_loop.run.assert_called_once_with("do something")
    assert result.status == "succeeded"


def test_routes_to_reflexion():
    with patch("critique_executor.executor.ReflexionLoop") as mock_loop_cls:
        mock_loop = MagicMock()
        mock_loop.run.return_value = _make_accepted_trace(CritiqueTopology.REFLEXION)
        mock_loop_cls.return_value = mock_loop

        runner = CritiqueExecutorRunner("reflexion")
        result = runner.run("do something")

    mock_loop_cls.assert_called_once()
    assert result.status == "succeeded"


def test_returns_runtime_result_with_metadata():
    with patch("critique_executor.executor.AdversarialLoop") as mock_loop_cls:
        mock_loop = MagicMock()
        mock_loop.run.return_value = _make_accepted_trace(CritiqueTopology.ADVERSARIAL)
        mock_loop_cls.return_value = mock_loop

        runner = CritiqueExecutorRunner("adversarial")
        result = runner.run("goal")

    assert result.runtime_name == "critique_executor"
    assert result.runtime_kind == "subprocess"
    assert isinstance(result.metadata, dict)
    assert result.started_at
    assert result.finished_at


def test_rejected_returns_rejected_status():
    with patch("critique_executor.executor.AdversarialLoop") as mock_loop_cls:
        mock_loop = MagicMock()
        mock_loop.run.return_value = _make_rejected_trace(CritiqueTopology.ADVERSARIAL)
        mock_loop_cls.return_value = mock_loop

        runner = CritiqueExecutorRunner("adversarial")
        result = runner.run("goal")

    assert result.status == "rejected"
    assert result.exit_code == 1


def test_exception_returns_failed_status():
    with patch("critique_executor.executor.AdversarialLoop") as mock_loop_cls:
        mock_loop = MagicMock()
        mock_loop.run.side_effect = RuntimeError("something broke")
        mock_loop_cls.return_value = mock_loop

        runner = CritiqueExecutorRunner("adversarial")
        result = runner.run("goal")

    assert result.status == "failed"
    assert result.error_summary is not None
    assert "something broke" in result.error_summary


def test_max_rounds_override():
    with patch("critique_executor.executor.AdversarialLoop") as mock_loop_cls:
        mock_loop = MagicMock()
        mock_loop.run.return_value = _make_accepted_trace(CritiqueTopology.ADVERSARIAL)
        mock_loop_cls.return_value = mock_loop

        runner = CritiqueExecutorRunner("adversarial")
        runner.run("goal", max_rounds=3)

    assert runner._config.max_rounds == 3


def test_criteria_override():
    with patch("critique_executor.executor.ReflexionLoop") as mock_loop_cls:
        mock_loop = MagicMock()
        mock_loop.run.return_value = _make_accepted_trace(CritiqueTopology.REFLEXION)
        mock_loop_cls.return_value = mock_loop

        runner = CritiqueExecutorRunner("reflexion")
        runner.run("goal", criteria=["be concise"])

    assert runner._config.criteria == ["be concise"]


def test_worker_backend_set_on_config():
    runner = CritiqueExecutorRunner("adversarial", worker_backend="codex_cli")
    assert runner._config.worker_backend == "codex_cli"


def test_working_dir_set_on_config():
    runner = CritiqueExecutorRunner("reflexion", working_dir="/some/path")
    assert runner._config.working_dir == "/some/path"
