# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from critique_executor.adversarial import AdversarialLoop
from critique_executor.models import CritiqueConfig, CritiqueTopology
from critique_executor.reflexion import ReflexionLoop


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CritiqueExecutorRunner:
    def __init__(
        self,
        topology: str,
        config: CritiqueConfig | None = None,
        worker_backend: Literal["claude_code", "codex_cli"] = "claude_code",
        working_dir: str = ".",
    ) -> None:
        self._topology = CritiqueTopology(topology)
        self._worker_backend = worker_backend
        self._working_dir = working_dir

        if config is not None:
            self._config = config
        else:
            self._config = CritiqueConfig(
                topology=self._topology,
                working_dir=working_dir,
                worker_backend=worker_backend,
            )

    def run(
        self,
        goal_text: str,
        max_rounds: int | None = None,
        criteria: list[str] | None = None,
    ):
        """Route to AdversarialLoop or ReflexionLoop. Return RxP RuntimeResult."""
        from rxp.contracts import RuntimeResult

        if max_rounds is not None:
            self._config.max_rounds = max_rounds
        if criteria is not None:
            self._config.criteria = criteria

        started_at = _now_iso()
        invocation_id = f"critique-{self._topology.value}-{started_at}"

        try:
            if self._topology == CritiqueTopology.ADVERSARIAL:
                loop = AdversarialLoop(self._config)
            else:
                loop = ReflexionLoop(self._config)

            trace = loop.run(goal_text)
            finished_at = _now_iso()

            status = "succeeded" if trace.accepted else "rejected"
            evidence = trace.to_evidence_dict()

            return RuntimeResult(
                invocation_id=invocation_id,
                runtime_name="critique_executor",
                runtime_kind="subprocess",
                status=status,
                exit_code=0 if trace.accepted else 1,
                started_at=started_at,
                finished_at=finished_at,
                error_summary=None,
                metadata={k: str(v) for k, v in evidence.items()},
            )

        except Exception as exc:
            finished_at = _now_iso()
            return RuntimeResult(
                invocation_id=invocation_id,
                runtime_name="critique_executor",
                runtime_kind="subprocess",
                status="failed",
                exit_code=1,
                started_at=started_at,
                finished_at=finished_at,
                error_summary=str(exc)[:500],
                metadata={},
            )
