# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import json
from typing import Literal

from core_runner.process import safe_run

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
    round_num: int,
    working_dir: str = ".",
    timeout_seconds: int = 3600,
    effort: str | None = None,
    backend: Literal["claude_code", "codex_cli"] = "claude_code",
) -> CritiqueVerdict:
    """Ask critic to evaluate proposal via CLI subprocess. Returns CritiqueVerdict.

    Critic does NOT know who the draft agent is (isolation invariant).
    Criteria listed explicitly in prompt.
    Response must be JSON {"status": "accept"|"reject", "reason": "..."}.
    """
    criteria_block = "\n".join(f"- {c}" for c in criteria) if criteria else "(none specified)"

    prompt = _CRITIC_PROMPT_TEMPLATE.format(
        goal_text=goal_text,
        criteria_block=criteria_block,
        proposal=proposal,
    )

    if backend == "codex_cli":
        response_text = _codex_critic(prompt, critic_model, working_dir, timeout_seconds, effort)
    else:
        response_text = _claude_critic(
            prompt, critic_model, critic_system_prompt, working_dir, timeout_seconds, effort
        )

    return parse_verdict(response_text, round_num)


def _claude_critic(
    prompt: str,
    model: str,
    system_prompt: str,
    working_dir: str,
    timeout_seconds: int,
    effort: str | None,
) -> str:
    cmd = [
        "claude",
        "--model", model,
        "--message", prompt,
        "--no-auto-commits",
        "--output-format", "json",
    ]
    if effort:
        cmd += ["--effort", effort]
    if system_prompt:
        cmd += ["--append-system-prompt", system_prompt]

    try:
        result = safe_run(cmd, cwd=working_dir, timeout_seconds=timeout_seconds)
    except FileNotFoundError:
        return '{"status": "reject", "reason": "claude CLI not found"}'
    if result.timed_out:
        return '{"status": "reject", "reason": "critic timed out"}'
    raw = result.stdout or result.stderr
    try:
        data = json.loads(raw)
        return data.get("result", raw)
    except (json.JSONDecodeError, AttributeError):
        return raw


def _codex_critic(
    prompt: str,
    model: str,
    working_dir: str,
    timeout_seconds: int,
    effort: str | None,
) -> str:
    cmd = ["codex", "--model", model, "--approval-mode", "full-auto"]
    if effort:
        cmd += ["-c", f'model_reasoning_effort="{effort}"']
    cmd += ["-q", prompt]
    try:
        result = safe_run(cmd, cwd=working_dir, timeout_seconds=timeout_seconds)
    except FileNotFoundError:
        return '{"status": "reject", "reason": "codex CLI not found"}'
    if result.timed_out:
        return '{"status": "reject", "reason": "critic timed out"}'
    return result.stdout or result.stderr
