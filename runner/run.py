#!/usr/bin/env python3
"""
OpenFang prototype runner — powers django-minion using Groq.
Runs inside Docker (tools on system PATH) or locally (pass --venv-bin).
"""
import argparse
import json
import os
import sys

from groq import Groq
from tools import TOOL_DEFINITIONS, execute_tool

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAND_DIR = os.path.join(BASE_DIR, "django-minion")

# Inside Docker all tools are on PATH; locally override with --venv-bin
DEFAULT_BIN = ""


def load_hand_context():
    with open(os.path.join(HAND_DIR, "SKILL.md")) as f:
        skill = f.read()
    # Write a clean system message — do NOT pass system_prompt.txt which contains
    # bash("...") pseudocode that confuses Groq's tool-calling parser.
    system_prompt = (
        "You are django-minion, an autonomous coding agent for Django projects.\n"
        "You detect and fix failing tests and lint errors, then open a pull request.\n\n"
        "## Rules\n"
        "- Always use your tools (bash, file_read, file_write) — never output commands as plain text.\n"
        "- Never touch migrations/, .env, settings/production.py, secrets.py.\n"
        "- Never push to main. Create a branch prefixed with 'minion/'.\n"
        "- Escalate (stop + explain) if confidence < 65% or files to change > 8.\n"
        "- Max 2 retries if tests still fail after a fix.\n"
        "- When done: print a full PR description (title, root cause, files changed, test results, confidence %).\n"
    )
    return system_prompt, skill


def build_user_message(app_path, bin_prefix):
    flake8  = f"{bin_prefix}flake8"  if bin_prefix else "flake8"
    python  = f"{bin_prefix}python"  if bin_prefix else "python"
    black   = f"{bin_prefix}black"   if bin_prefix else "black"
    isort   = f"{bin_prefix}isort"   if bin_prefix else "isort"

    return f"""
LOCAL TEST MODE — one-shot run
================================
Skip Phase 1 (GitHub CI polling). The Django app is already on disk.

Django app path : {app_path}
Django app name : myapp

Your job (phases 2-5):
1. Run flake8 and pytest — treat output as CI failure logs.
2. Diagnose each failure, rate your confidence.
3. Fix the code with file_write. Do NOT touch migrations/, .env, settings/production.py.
4. Re-run linting and tests to confirm all pass.
5. Create a git branch (prefix: minion/), commit, then PRINT the full PR description
   to the console. Do NOT call the GitHub API.

Tool commands to use:
  flake8 : {flake8}
  python : {python}
  black  : {black}
  isort  : {isort}

Start with these two commands now:
  cd {app_path} && {flake8} myapp/ --max-line-length=88 --exclude=migrations
  cd {app_path} && {python} -m pytest myapp/ -v --tb=short
""".strip()


def run_agent(app_path, bin_prefix):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY environment variable not set.")
        sys.exit(1)

    system_prompt, skill = load_hand_context()
    system = system_prompt + "\n\n---\n\n# SKILL REFERENCE\n\n" + skill

    client = Groq(api_key=api_key)
    messages = [{"role": "user", "content": build_user_message(app_path, bin_prefix)}]

    model = "llama-3.3-70b-versatile"

    print("=" * 60)
    print("  django-minion — OpenFang prototype run")
    print("=" * 60)
    print(f"  Target app : {app_path}")
    print(f"  Model      : {model} (Groq)")
    print("=" * 60 + "\n")

    iteration = 0
    max_iterations = 40

    while iteration < max_iterations:
        iteration += 1

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}] + messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            max_tokens=4096,
            temperature=0.1,
        )

        choice = response.choices[0]
        msg = choice.message

        assistant_entry = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            assistant_entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        messages.append(assistant_entry)

        if msg.content:
            print(f"\n🤖  {msg.content}\n")

        if choice.finish_reason == "stop" or not msg.tool_calls:
            print("\n✅  Agent run complete.")
            break

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            arg_display = json.dumps(args, ensure_ascii=False)
            if len(arg_display) > 120:
                arg_display = arg_display[:120] + "…"
            print(f"🔧  {name}({arg_display})")

            result = execute_tool(name, args)

            preview = result[:400].replace("\n", "\n    ")
            print(f"    ↳ {preview}")
            if len(result) > 400:
                print(f"    … ({len(result)} chars total)")
            print()

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    if iteration >= max_iterations:
        print("\n⚠️  Hit max iterations limit. Stopping.")


def main():
    parser = argparse.ArgumentParser(description="OpenFang django-minion runner")
    parser.add_argument(
        "--app",
        default=os.path.join(BASE_DIR, "test-django-app"),
        help="Path to the Django app (default: ../test-django-app)",
    )
    parser.add_argument(
        "--venv-bin",
        default="",
        help="Path to venv bin dir with trailing slash, e.g. /opt/venv/bin/ (local only)",
    )
    args = parser.parse_args()
    run_agent(os.path.abspath(args.app), args.venv_bin)


if __name__ == "__main__":
    main()
