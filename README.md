# Tessa

A local AI coding agent for your terminal. No API keys, no cloud — everything
runs on your machine through [Ollama](https://ollama.com).

```
╭─ TESSA ─────────────────────────╮
│ model    qwen3.5:9b             │
│ project  Python                 │
╰── local AI coding agent v0.1.0 ─╯

Tessa > explain this project
```

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) with at least one model pulled
  (`ollama pull qwen3.5`)

## Install

```bash
git clone <this repo> && cd tessa
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
ln -s "$PWD/.venv/bin/tessa" /opt/homebrew/bin/tessa   # or anywhere on your PATH
```

## Usage

| Command | What it does |
|---|---|
| `tessa` | Interactive chat with your codebase context |
| `tessa ask "why is this failing?"` | One-shot question |
| `tessa analyze` | Project summary: languages, size, key files |
| `tessa models` | List installed Ollama models |
| `tessa init` | Create `.tessa/` project config |
| `tessa config show` | Show effective config |
| `tessa config set model qwen3.5:9b` | Set a config value (`--project` for per-repo) |

Inside chat: `/help`, `/model <name>`, `/models`, `/new`, `/exit`.

## Configuration

Layered JSON config — project overrides global:

- `~/.tessa/config.json` — global defaults
- `<project>/.tessa/config.json` — per-repository (created by `tessa init`)

Keys: `model` (default: auto-pick best installed coder model), `temperature`,
`num_ctx`, `ollama_host`, `think` (`auto`/`on`/`off` — reasoning for thinking
models like qwen3; `off` gives much faster replies), `permission_mode`.

## Architecture

```
src/tessa/
├── cli/       Typer commands, chat REPL, Rich rendering
├── config/    layered JSON settings
├── llm/       Ollama HTTP client, streaming, model selection
├── agent/     prompts, conversation memory   (agent loop: Milestone 3)
├── context/   repository scanner             (retrieval: Milestone 2)
└── tools/     filesystem / terminal / git tools (Milestones 3–5)
```

## Roadmap

- [x] **M1** — packaged CLI, streaming chat, config, project analysis
- [ ] **M2** — code indexing and retrieval (embeddings via Ollama)
- [ ] **M3** — agent loop with tool calling and safe file editing
- [ ] **M4** — command execution with a permission system
- [ ] **M5** — git workflows: diff review, commit generation, push
- [ ] **M6** — persistent project memory
- [ ] **M7** — plugins

## Development

```bash
.venv/bin/pytest
```
