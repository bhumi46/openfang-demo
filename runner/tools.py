import os
import subprocess
import requests


def execute_tool(name, args):
    if name == "bash":
        return tool_bash(args.get("command", ""))
    elif name == "file_read":
        return tool_file_read(args.get("path", ""))
    elif name == "file_write":
        return tool_file_write(args.get("path", ""), args.get("content", ""))
    elif name == "web_fetch":
        return tool_web_fetch(
            args.get("url", ""),
            args.get("method", "GET"),
            args.get("body"),
            args.get("headers", {}),
        )
    elif name == "web_search":
        return f"[web_search not available in local test mode] Query: {args.get('query', '')}"
    return f"Unknown tool: {name}"


def tool_bash(command):
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=60
        )
        output = (result.stdout + result.stderr).strip()
        return output[:4000] if output else "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after 60 seconds"
    except Exception as e:
        return f"ERROR: {e}"


def tool_file_read(path):
    try:
        with open(path) as f:
            return f.read()
    except Exception as e:
        return f"ERROR reading {path}: {e}"


def tool_file_write(path, content):
    try:
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"OK: wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"ERROR writing {path}: {e}"


def tool_web_fetch(url, method="GET", body=None, headers=None):
    try:
        token = os.environ.get("GITHUB_TOKEN", "")
        h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
        if headers:
            h.update(headers)
        resp = requests.request(method, url, json=body, headers=h, timeout=30)
        return resp.text[:4000]
    except Exception as e:
        return f"ERROR: {e}"


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command and return stdout+stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_read",
            "description": "Read a file from the local filesystem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative file path"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_write",
            "description": "Write content to a file (overwrites if exists).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Make an HTTP request (GET/POST) to a URL, e.g. GitHub API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "method": {"type": "string", "default": "GET"},
                    "body": {"type": "object"},
                    "headers": {"type": "object"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information about an error or library.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"],
            },
        },
    },
]
