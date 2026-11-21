# Security Policy

elliotAI drives a real browser to user-supplied URLs and sends page content to LLMs,
so security reports are welcome.

## Reporting a vulnerability

Please **do not open a public issue**. Use GitHub's private
[security advisory](https://github.com/Jinish2170/elliotAI/security/advisories/new) form.
Include the affected component, steps to reproduce, and impact. You can expect an
acknowledgement within 5 working days.

## In scope
- Server-side request forgery via audit targets (see `backend/services/guards.py`)
- Prompt injection that changes a verdict or extracted facts (see `elliot/core/injection.py`)
- Secret leakage through logs, traces or API responses
- Abuse of the public API (rate-limit or tier-allowlist bypass)

## Out of scope
- Findings that require a compromised host or a malicious local operator
- Missing security headers on third-party sites audited by elliotAI (that is the product's output)

## Using elliotAI on sites you do not own
Audits are passive (navigation and screenshots only; no form submission). Only audit
sites you are permitted to analyse, and respect their terms of service.
