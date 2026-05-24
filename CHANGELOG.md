# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Unit tests for `agent_runner.run_agent` and `critic_runner.run_critic`
  under `tests/unit/`, exercising command construction, JSON parsing, and
  timeout / missing-CLI fallbacks with subprocess/`safe_run` mocked.
- Venv guard in `tests/conftest.py` (skipped in CI).
- `.hooks/pre-commit` enforcing `.console/log.md` updates on source changes.
- `CHANGELOG.md` and expanded `README.md` (what-this-repo-is / is-not,
  quick start, architecture).

### Changed
- Extracted the shared propose→critique round loop into
  `critique_executor._loop.run_critique_loop`; `AdversarialLoop` and
  `ReflexionLoop` now delegate to it instead of carrying duplicate bodies.

### Fixed
- `.gitignore` now follows the managed-workspace `.console/*` + `CLAUDE.md`
  policy.
