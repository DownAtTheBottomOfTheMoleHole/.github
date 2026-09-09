# Repository guidance

This repository holds organisation community defaults and reusable AI assets.
Follow the user's requested scope, existing authorisation, and repository conventions.
Read `CONTRIBUTING.md` for contribution standards. Preserve unrelated working changes.

## AI assets

- Author agents, skills, prompts, and instructions under `.github/`.
- `agents/` contains generated organisation discovery copies. After editing an agent,
  run `python3 tools/sync_ai_assets.py`; do not edit generated copies directly.
- `.agents/skills/` exposes the canonical skills to Codex through relative symlinks.
- Read only the skill and supporting references relevant to the current task.
  Instructions packaged as examples or overlays are not blanket requirements for every task.
- Use the model selected by the user and tools available in the current session.
  Do not pin obsolete models, invent tool access, or bypass host permissions.
- Complete authorised, reversible work and relevant verification. Ask only for missing
  decisions that materially affect correctness or for authority not already supplied.
- Resolve asset paths from this checkout, and distinguish it from a consumer repository.
  An organisation agent being discoverable does not prove its companion scripts are installed.

## Validation

Use Python 3.10 or later. Install validation dependencies with
`python3 -m pip install -r tools/requirements-dev.txt`.
Run `python3 tools/validate_ai_assets.py` and
`python3 -m unittest discover -s tests -v` before completing changes.
Script tests use mocks; do not authenticate or create remote resources to test AI assets.
Install runtime dependencies only when the script or tests require them.

## Code Review Rules

Prioritise real capability and correctness failures: unreachable tools, stale model
restrictions, broken asset discovery/links, conflicting instructions, nonfunctional previews,
unvalidated target identifiers, and duplicate or unintended remote writes on retry.
Report path, trigger, impact, and supporting evidence. Keep infrastructure/business assessment
separate from a code correctness verdict. Never claim live execution succeeded from a static check.
