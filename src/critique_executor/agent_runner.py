# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import json
import subprocess
from typing import Literal


def run_agent(
    goal_text: str,
    working_dir: str,
    model: str,
    system_prompt: str = "",
    rejection_reason: str | None = None,
    timeout_seconds: int = 3600,
    effort: str | None = None,
    backend: Literal["claude_code", "codex_cli"] = "claude_code",
) -> tuple[bool, str]:
    """Run agent subprocess. Returns (success, stdout).

    Adversarial: proposer never sees critic identity or system prompt.
    Only rejection_reason is passed if provided.
    D1: goal_text is the primary --message, not re-framed.
    """
    message = goal_text
    if rejection_reason:
        message = f"{goal_text}\n\n---\nPrevious critique: {rejection_reason}\nPlease revise."

    if backend == "codex_cli":
        cmd = [
            "codex",
            "--model", model,
            "--approval-mode", "full-auto",
        ]
        if effort:
            cmd += ["-c", f'model_reasoning_effort="{effort}"']
        cmd += ["-q", message]
    else:
        cmd = [
            "claude",
            "--message", message,
            "--no-auto-commits",
            "--output-format", "json",
            "--model", model,
        ]
        if effort:
            cmd += ["--effort", effort]
        if system_prompt:
            cmd += ["--append-system-prompt", system_prompt]

    try:
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        if result.returncode != 0:
            return False, result.stdout or result.stderr

        if backend == "codex_cli":
            output = result.stdout
        else:
            # Claude Code JSON output has a result field when successful
            try:
                data = json.loads(result.stdout)
                output = data.get("result", result.stdout)
            except (json.JSONDecodeError, AttributeError):
                output = result.stdout

        return True, output

    except subprocess.TimeoutExpired:
        return False, f"agent timed out after {timeout_seconds}s"
    except FileNotFoundError:
        return False, f"{'codex' if backend == 'codex_cli' else 'claude'} CLI not found"
