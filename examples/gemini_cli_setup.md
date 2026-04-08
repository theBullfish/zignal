# Gemini CLI Integration Guide

This guide explains how to set up Zignal as a permanent memory for the [Gemini CLI](https://github.com/google/gemini-cli).

## Prerequisites

- Python 3.9+
- Gemini CLI installed and configured

## 1. Installation

On many Linux systems, installing Python packages globally is restricted. We recommend using a local virtual environment within the Zignal directory.

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/milla-jovovich/zignal.git
cd zignal

# Create a virtual environment
python3 -m venv .venv

# Install dependencies and Zignal in editable mode
.venv/bin/pip install -e .
```

## 2. Initialization

Set up your "Palace" (the database) and configure your identity.

```bash
# Initialize the palace in the current directory
.venv/bin/python3 -m zignal init .
```

### Identity and Wings (Optional but Recommended)
You can manually define who you are and what projects you work on by creating/editing these files in `~/.zignal/`:

- **`~/.zignal/identity.txt`**: A plain text file describing your role and focus.
- **`~/.zignal/wing_config.json`**: A JSON file mapping projects and name variants to "Wings".

## 3. Connect to Gemini CLI (MCP)

Register Zignal as an MCP server so Gemini CLI can use its tools.

```bash
gemini mcp add zignal /absolute/path/to/zignal/.venv/bin/python3 -m zignal.mcp_server --scope user
```
*Note: Use the absolute path to ensure it works from any directory.*

## 4. Enable Auto-Saving (Hooks)

To ensure the AI saves memories automatically when conversation history becomes too long, add a `PreCompress` hook to your Gemini CLI settings.

Edit your `~/.gemini/settings.json` and add the following:

```json
{
  "hooks": {
    "PreCompress": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "/absolute/path/to/zignal/hooks/zignal_precompact_hook.sh"
          }
        ]
      }
    ]
  }
}
```

Make sure the hook scripts are executable:
```bash
chmod +x hooks/*.sh
```

## 5. Usage

Once connected, Gemini CLI will automatically:
- Start the Zignal server on launch.
- Use `zignal_search` to find relevant past discussions.
- Use the `PreCompress` hook to save new memories before they are lost.

### Manual Mining
If you want the AI to learn from your existing code or docs immediately, run the "mine" command:
```bash
.venv/bin/python3 -m zignal mine /path/to/your/project
```

### Verification
In a Gemini CLI session, you can run:
- `/mcp list`: Verify `zignal` is `CONNECTED`.
- `/hooks panel`: Verify the `PreCompress` hook is active.
