# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main`  | ✅ Yes     |

Only the current `main` branch receives security fixes.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report security issues privately by emailing **coding.projects.1642@proton.me**.

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations (optional)

You will receive an acknowledgment within 72 hours. We aim to release a fix within 14 days of a confirmed report, depending on severity and complexity.

## Scope

CritiqueExecutor runs adversarial and reflexion critique loops for iterative AI task refinement. The primary security surface is:

- **Critic isolation bypass** — anything that exposes proposer/agent identity to the critic prompt
- **API token exposure** via config files or logs (`ANTHROPIC_API_KEY`)
- **Round limit bypass** — circumventing the hard cap of 10 rounds in `CritiqueConfig`
- **Prompt injection** — untrusted critique content reaching subsequent agent rounds
- **Log injection** via untrusted verdict or trace content written to structured logs

## Out of Scope

- Vulnerabilities in upstream AI providers or Claude Code
- Issues requiring physical access to the host machine
- Denial-of-service via normal task load (rate limiting is a configuration concern)
