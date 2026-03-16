# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

An OpenFang "Hand" — a reusable autonomous coding agent template called `django-minion`. It monitors Django projects via GitHub Actions and automatically fixes failing tests/lint issues by creating PRs. There is no traditional build system; deployment is via the `openfang` CLI.

## OpenFang CLI Commands

```bash
# Install and activate the Hand
openfang hand install ./django-minion/
openfang hand activate django-minion \
  --set github_repo="org/repo" \
  --set slack_channel="#django-alerts" \
  --set django_app="myapp"

# Operate the Hand
openfang hand run django-minion --once   # manual one-shot run
openfang logs django-minion --follow     # stream logs
openfang hand status django-minion
openfang hand pause django-minion
openfang hand resume django-minion
openfang hand deactivate django-minion
```

Requires OpenFang v0.3.x+.

## Core Files

| File | Purpose |
|------|---------|
| `django-minion/HAND.toml` | Schedule, tools, guardrails, required settings |
| `django-minion/system_prompt.txt` | 5-phase operating procedure injected into the agent |
| `django-minion/SKILL.md` | Django error patterns, safe/unsafe edit rules, quality gates |

## Agent Architecture

The agent runs on a 3-hour cron (`0 */3 * * *`, Asia/Kolkata). Each run follows five phases encoded in `system_prompt.txt`:

1. **OBSERVE** — Poll GitHub Actions for failing CI runs and open issues
2. **DIAGNOSE** — Fetch logs, read failing code, compute confidence score
3. **FIX** — Create a `minion/` branch, write fix, run linting + tests locally
4. **PULL REQUEST** — Push branch, open GitHub PR
5. **REPORT** — Post summary to Slack and OpenFang dashboard

## Guardrails (defined in HAND.toml)

- **Never touch:** `settings/production.py`, `.env`, `migrations/`, `secrets.py`
- **Escalate if:** confidence < 65%, or files to change > 8
- **Require approval for:** `git push --force`, `DROP TABLE`, `DELETE FROM`
- **Max PRs per run:** 3
- **Max CI retries:** 2 (then abandon branch)

## Linting/Testing Commands (run by the agent on the target Django repo)

```bash
flake8 {django_app}/ --max-line-length=88 --exclude=migrations
black --check {django_app}/        # check; black {django_app}/ to fix
isort --check-only {django_app}/   # check; isort {django_app}/ to fix
python manage.py check --deploy
python -m pytest {django_app}/ -v --tb=short -x
```

## Required Settings

Configure via `openfang hand activate --set key=value`:

| Setting | Required | Default |
|---------|----------|---------|
| `github_repo` | Yes | — |
| `github_token` | Yes (secret) | — |
| `slack_channel` | No | `#django-alerts` |
| `django_app` | No | `myapp` |
| `branch_prefix` | No | `minion/` |
| `python_version` | No | `3.11` |
