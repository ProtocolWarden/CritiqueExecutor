# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from critique_executor.models import CritiqueVerdict
from critique_executor.verdict import parse_verdict

_CRITIC_PROMPT_TEMPLATE = """\
You are evaluating a proposal against a goal.

Goal:
{goal_text}

Criteria:
{criteria_block}

Proposal to evaluate:
{proposal}

Respond with valid JSON only: {{"status": "accept" or "reject", "reason": "<explanation>"}}
Do not include any other text."""


def run_critic(
    proposal: str,
    goal_text: str,
    criteria: list[str],
    critic_model: str,
    critic_system_prompt: str,
    anthropic_client: object,
    round_num: int,
) -> CritiqueVerdict:
    """Ask critic to evaluate proposal. Returns CritiqueVerdict.

    Critic does NOT know who the proposer is (isolation invariant).
    Criteria listed explicitly in prompt.
    Response must be JSON {"status": "accept"|"reject", "reason": "..."}.
    """
    criteria_block = "\n".join(f"- {c}" for c in criteria) if criteria else "(none specified)"

    user_content = _CRITIC_PROMPT_TEMPLATE.format(
        goal_text=goal_text,
        criteria_block=criteria_block,
        proposal=proposal,
    )

    messages_kwargs: dict = {
        "model": critic_model,
        "max_tokens": 512,
        "messages": [{"role": "user", "content": user_content}],
    }
    if critic_system_prompt:
        messages_kwargs["system"] = critic_system_prompt

    response = anthropic_client.messages.create(**messages_kwargs)  # type: ignore[union-attr]
    response_text = response.content[0].text
    return parse_verdict(response_text, round_num)
