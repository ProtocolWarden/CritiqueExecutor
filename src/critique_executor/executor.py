# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import os
from datetime import datetime, timezone

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
        api_key: str | None = None,
    ) -> None:
        self._topology = CritiqueTopology(topology)
        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

        import anthropic
        self._client = anthropic.Anthropic(api_key=resolved_key)

        if config is not None:
            self._config = config
        else:
            self._config = CritiqueConfig(topology=self._topology)

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
                loop = AdversarialLoop(self._config, self._client)
            else:
                loop = ReflexionLoop(self._config, self._client)

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
