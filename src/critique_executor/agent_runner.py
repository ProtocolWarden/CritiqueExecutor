# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import json
import subprocess


def run_agent(
    goal_text: str,
    working_dir: str,
    system_prompt: str = "",
    rejection_reason: str | None = None,
    timeout_seconds: int = 3600,
) -> tuple[bool, str]:
    """Run Claude Code subprocess. Returns (success, stdout).

    Adversarial: proposer never sees critic identity or system prompt.
    Only rejection_reason is passed if provided.
    D1: goal_text is the primary --message, not re-framed.
    """
    message = goal_text
    if rejection_reason:
        message = f"{goal_text}\n\n---\nPrevious critique: {rejection_reason}\nPlease revise."

    cmd = [
        "claude",
        "--message", message,
        "--no-auto-commits",
        "--output-format", "json",
    ]

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
        return False, "claude CLI not found"
