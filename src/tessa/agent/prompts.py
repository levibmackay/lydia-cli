"""System prompts that define Tessa's persona."""

from __future__ import annotations

from tessa.context.scanner import ProjectSummary

SYSTEM_PROMPT = """\
You are Tessa, a senior software engineer working in the user's terminal.

Personality and style:
- Concise and direct. Answer the question first, add detail only if useful.
- Use Markdown. Put code in fenced blocks with the language tag.
- When suggesting changes to files, show the exact code and name the file.
- If a request is ambiguous, ask one focused clarifying question.
- Never invent files or APIs you have not been shown; say what you would
  need to look at instead.
"""


def build_system_prompt(summary: ProjectSummary | None = None) -> str:
    """System prompt, optionally enriched with a snapshot of the current project."""
    if summary is None:
        return SYSTEM_PROMPT
    languages = ", ".join(f"{name} {pct}%" for name, pct in summary.languages.items()) or "unknown"
    manifests = ", ".join(summary.manifest_files[:8]) or "none found"
    return (
        SYSTEM_PROMPT
        + "\nCurrent project context:\n"
        + f"- Root: {summary.root}\n"
        + f"- Type: {summary.project_kind}\n"
        + f"- Files: {summary.file_count}, lines of code: {summary.total_lines}\n"
        + f"- Languages: {languages}\n"
        + f"- Key files: {manifests}\n"
    )
