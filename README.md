# django-minion

**A Stripe Minions-style autonomous coding agent for Python Django projects — built on OpenFang.**

Monitors your Django repo every 3 hours. Detects failing tests and linting errors.
Writes fixes, runs the test suite, and opens a GitHub PR — with no human interaction
between trigger and pull request.

---

## What it does

- Polls your GitHub Actions CI for failing runs every 3 hours
- Classifies failures: test failure, lint error, migration warning, or infra issue
- Writes the fix, runs `flake8`, `black`, `pytest`, and `manage.py check`
- Opens a GitHub PR with a full description, confidence score, and test results
- Posts a summary to your Slack channel
- Escalates anything it cannot fix confidently (max 2 retries, max 8 files)

---

## Prerequisites

| Requirement | Version |
|---|---|
| Linux / macOS / Windows | any |
| Python + Django project | Django 4.x / 5.x |
| GitHub repository | with Actions CI enabled |
| OpenFang | v0.3.x or later |
| LLM API key | Groq (free), Anthropic, or any of 27 providers |

---

## Step-by-step setup

### Step 1 — Install OpenFang

```bash
curl -fsSL https://openfang.sh/install | sh
```

Verify:

```bash
openfang --version
```

---

### Step 2 — Initialise OpenFang

```bash
openfang init
```

This walks you through setting your default LLM provider.
For a free start, choose **Groq** and paste your key from console.groq.com.

Start the daemon:

```bash
openfang start
# Dashboard now live at http://localhost:4200
```

---

### Step 3 — Clone or download this Hand

```bash
git clone https://github.com/your-org/django-minion-hand.git
cd django-minion-hand
```

The hand directory contains exactly three files:

```
django-minion/
├── HAND.toml        ← job description (schedule, tools, guardrails)
├── system_prompt.txt ← 5-phase operating procedure (the blueprint)
└── SKILL.md         ← Django domain knowledge injected at runtime
```

---

### Step 4 — Set your secrets as environment variables

**Never put secrets in HAND.toml.**

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
export GROQ_API_KEY="gsk_xxxxxxxxxxxxxxxxxxxx"   # or ANTHROPIC_API_KEY etc.
```

For permanent setup, add these to your `~/.bashrc` or `~/.zshrc`.

---

### Step 5 — Make sure your Django repo is locally available

The minion uses `bash` to run git, pytest, and Django commands.
Your repo must be checked out on the same machine where OpenFang is running.

```bash
cd /path/to/your/django-project
pip install -r requirements.txt
pip install flake8 black isort pytest pytest-django
python manage.py check   # should show no errors
python -m pytest myapp/ -v   # should run (pass or fail is OK)
```

Configure your `pytest.ini` or `setup.cfg`:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = myproject.settings.test
python_files = tests.py test_*.py *_tests.py
```

---

### Step 6 — Install and activate the Hand

```bash
# Install from local directory
openfang hand install ./django-minion/

# Activate with your settings
openfang hand activate django-minion \
  --set github_repo="your-org/your-django-repo" \
  --set slack_channel="#django-alerts" \
  --set django_app="myapp"
```

---

### Step 7 — Test it manually once

Before waiting for the cron schedule, trigger a one-shot run:

```bash
openfang hand run django-minion --once
```

Watch the logs:

```bash
openfang logs django-minion --follow
```

Open the dashboard to see the run report:

```
http://localhost:4200
```

---

### Step 8 — Let it run autonomously

The hand is now active. It will run automatically every 3 hours per the cron schedule
in `HAND.toml`. You will receive:

- A Slack message when a PR is opened (with link)
- A Slack message when something is escalated
- A "✅ All clear" message when no failures are found

---

## Useful commands

```bash
# Check current status
openfang hand status django-minion

# Pause without losing state
openfang hand pause django-minion

# Resume
openfang hand resume django-minion

# View recent logs
openfang logs django-minion

# Deactivate permanently
openfang hand deactivate django-minion

# Update settings
openfang hand activate django-minion --set slack_channel="#new-channel"
```

---

## How it maps to Stripe Minions

| Stripe concept | This hand |
|---|---|
| Devbox (AWS EC2) | Your local machine or any Linux VM |
| Toolshed MCP (~500 tools) | `bash`, `file_read`, `file_write`, `web_fetch`, `web_search` |
| Blueprint (deterministic + LLM) | System prompt phases (lint always runs, LLM writes the fix) |
| Cursor rule files | `SKILL.md` injected at runtime |
| Max 2 CI rounds | `max_ci_retries = 2` in `HAND.toml` |
| Escalate on failure | Slack alert via OpenFang channel adapter |
| Human review | GitHub PR — you approve and merge |

---

## Guardrails

The hand will **never**:

- Push directly to `main` or `develop`
- Merge its own pull requests
- Touch `migrations/`, `.env`, `settings/production.py`, or `secrets.py`
- Change more than 8 files in one PR
- Open more than 3 PRs per run
- Retry a failing fix more than 2 times

---

## Customising the Hand

Edit `HAND.toml` to change the schedule, tool list, or guardrails.
Edit `system_prompt.txt` to change the operating procedure.
Edit `SKILL.md` to add error patterns specific to your codebase.

After any edit, reinstall:

```bash
openfang hand install ./django-minion/ --force
openfang hand activate django-minion
```

---

## File structure

```
django-minion/
├── HAND.toml           schedule, tools, settings, guardrails, metrics
├── system_prompt.txt   5-phase SOP: Observe → Diagnose → Fix → PR → Report
└── SKILL.md            Django error patterns, GitHub API, quality gates
```

---

## Troubleshooting

**Hand not finding my repo**
Make sure `github_repo` is set to `org/repo` format and your `GITHUB_TOKEN`
has `repo` scope.

**pytest not found**
The `bash` tool uses your system PATH. Install pytest in the same virtualenv
the hand will use, or use an absolute path in the system prompt.

**Minion escalating everything**
Check your confidence threshold (65% default). If your codebase has unusual
patterns, add them to `SKILL.md` so the agent recognises them.

**Port 4200 already in use**
Edit `~/.openfang/config.toml` and change `port = 4201`.

---

## License

MIT — use it however you want.

---

## Built with

- [OpenFang](https://openfang.sh) — open-source Agent OS
- Inspired by [Stripe Minions](https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents)
