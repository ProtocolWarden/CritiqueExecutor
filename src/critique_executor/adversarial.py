# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from critique_executor.agent_runner import run_agent
from critique_executor.critic_runner import run_critic
from critique_executor.models import CritiqueConfig, CritiqueTopology, CritiqueTrace, VerdictStatus
from critique_executor.trace import CritiqueTraceBuilder


class AdversarialLoop:
    """Proposer + critic loop. Neither sees the other's system prompt."""

    def __init__(self, config: CritiqueConfig, anthropic_client: object) -> None:
        self._config = config
        self._client = anthropic_client

    def run(self, goal_text: str) -> CritiqueTrace:
        builder = CritiqueTraceBuilder(CritiqueTopology.ADVERSARIAL, goal_text)
        cfg = self._config
        last_rejection: str | None = None
        final_output: str | None = None
        accepted = False

        for round_num in range(1, cfg.max_rounds + 1):
            success, proposal = run_agent(
                goal_text=goal_text,
                working_dir=cfg.working_dir,
                system_prompt=cfg.proposer_system_prompt,
                rejection_reason=last_rejection,
                timeout_seconds=cfg.timeout_seconds,
            )

            if not success:
                # Agent failure counts as a reject round so the trace is complete
                from critique_executor.models import CritiqueVerdict
                verdict = CritiqueVerdict(
                    status=VerdictStatus.REJECT,
                    reason=f"agent run failed: {proposal[:200]}",
                    round=round_num,
                )
                builder.add_round(proposal, verdict)
                last_rejection = verdict.reason
                continue

            verdict = run_critic(
                proposal=proposal,
                goal_text=goal_text,
                criteria=cfg.criteria,
                critic_model=cfg.critic_model,
                critic_system_prompt=cfg.critic_system_prompt,
                anthropic_client=self._client,
                round_num=round_num,
            )
            builder.add_round(proposal, verdict)

            if verdict.status == VerdictStatus.ACCEPT:
                final_output = proposal
                accepted = True
                break

            last_rejection = verdict.reason

        return builder.build(final_output=final_output, accepted=accepted)
