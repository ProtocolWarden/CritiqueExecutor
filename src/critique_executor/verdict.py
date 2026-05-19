# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import json

from critique_executor.models import CritiqueVerdict, VerdictStatus


def parse_verdict(response_text: str, round_num: int) -> CritiqueVerdict:
    """Parse LLM response into CritiqueVerdict.

    Expected format: JSON {"status": "accept"|"reject", "reason": "..."}
    On parse failure: returns reject with reason=response_text[:200].
    """
    try:
        data = json.loads(response_text.strip())
        status = VerdictStatus(data["status"])
        reason = str(data.get("reason", ""))
        return CritiqueVerdict(status=status, reason=reason, round=round_num)
    except (json.JSONDecodeError, KeyError, ValueError):
        return CritiqueVerdict(
            status=VerdictStatus.REJECT,
            reason=response_text[:200],
            round=round_num,
        )
