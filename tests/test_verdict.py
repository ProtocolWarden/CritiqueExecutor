# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import json

from critique_executor.models import VerdictStatus
from critique_executor.verdict import parse_verdict


def test_valid_accept():
    text = json.dumps({"status": "accept", "reason": "looks good"})
    v = parse_verdict(text, round_num=1)
    assert v.status == VerdictStatus.ACCEPT
    assert v.reason == "looks good"
    assert v.round == 1


def test_valid_reject():
    text = json.dumps({"status": "reject", "reason": "incomplete"})
    v = parse_verdict(text, round_num=2)
    assert v.status == VerdictStatus.REJECT
    assert v.reason == "incomplete"
    assert v.round == 2


def test_malformed_json_returns_reject():
    v = parse_verdict("not json at all", round_num=3)
    assert v.status == VerdictStatus.REJECT
    assert v.round == 3


def test_malformed_json_reason_is_original_text():
    text = "definitely not json"
    v = parse_verdict(text, round_num=1)
    assert text in v.reason


def test_long_response_truncated_to_200():
    long_text = "x" * 500
    v = parse_verdict(long_text, round_num=1)
    assert v.status == VerdictStatus.REJECT
    assert len(v.reason) <= 200


def test_missing_status_field_returns_reject():
    text = json.dumps({"reason": "no status field"})
    v = parse_verdict(text, round_num=1)
    assert v.status == VerdictStatus.REJECT


def test_invalid_status_value_returns_reject():
    text = json.dumps({"status": "maybe", "reason": "unsure"})
    v = parse_verdict(text, round_num=1)
    assert v.status == VerdictStatus.REJECT


def test_whitespace_stripped_before_parse():
    text = "  " + json.dumps({"status": "accept", "reason": "ok"}) + "\n"
    v = parse_verdict(text, round_num=1)
    assert v.status == VerdictStatus.ACCEPT
