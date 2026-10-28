# Contributing

Create an isolated Python environment and install `-e ".[dev]"` using `-c constraints.txt`. Read AGENTS.md and SECURITY.md. Every change must document the problem, threat, behavior, compatibility, tests and limitations.

The v1 contract cannot be extended by simply ignoring unknown fields. Plan format migrations explicitly; never silently change the meaning of an existing version. Add a conformance vector and adversarial test for parser or protocol changes.

Versions follow PEP 440. A release candidate does not become a production release solely on the basis of local tests. See docs/RELEASE.md.
