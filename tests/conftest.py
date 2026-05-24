# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import os
import sys
import types
from pathlib import Path

# ---------------------------------------------------------------------------
# Venv guard: refuse to run against the wrong interpreter when a project
# .venv exists (skipped in CI, where the venv layout differs).
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent.resolve()
_EXPECTED_VENV = (_REPO_ROOT / ".venv").resolve()
_ACTIVE_PREFIX = Path(sys.prefix).resolve()
_IN_CI = os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS")

if _EXPECTED_VENV.is_dir() and not _IN_CI and _ACTIVE_PREFIX != _EXPECTED_VENV:
    raise SystemExit(
        f"ERROR: Tests must be run inside this project's virtual environment.\n"
        f"Expected: {_EXPECTED_VENV}\n"
        f"Active:   {_ACTIVE_PREFIX}\n\n"
        f"Activate it first:\n"
        f"  source .venv/bin/activate\n"
        f"Or invoke pytest through the venv directly:\n"
        f"  .venv/bin/pytest"
    )

# core_runner lives as a sibling repo; add its src/ to path so tests run
# without installing the package
_core_runner_src = Path(__file__).parent.parent.parent / "CoreRunner" / "src"
if str(_core_runner_src) not in sys.path:
    sys.path.insert(0, str(_core_runner_src))

# ---------------------------------------------------------------------------
# Stub rxp so tests can import executor without installing the package
# ---------------------------------------------------------------------------
_rxp = types.ModuleType("rxp")
_rxp_contracts = types.ModuleType("rxp.contracts")


class _RuntimeResult:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


_rxp_contracts.RuntimeResult = _RuntimeResult
_rxp_contracts.RuntimeInvocation = type("RuntimeInvocation", (), {})
_rxp_contracts.ArtifactDescriptor = type("ArtifactDescriptor", (), {})
_rxp.contracts = _rxp_contracts
sys.modules["rxp"] = _rxp
sys.modules["rxp.contracts"] = _rxp_contracts

# ---------------------------------------------------------------------------
# Stub cxrp
# ---------------------------------------------------------------------------
_cxrp = types.ModuleType("cxrp")
sys.modules["cxrp"] = _cxrp

# ---------------------------------------------------------------------------
# Stub anthropic so tests can import executor without the package installed
# ---------------------------------------------------------------------------
_anthropic = types.ModuleType("anthropic")


class _FakeAnthropicClient:
    def __init__(self, **kwargs):
        pass


_anthropic.Anthropic = _FakeAnthropicClient
sys.modules["anthropic"] = _anthropic
