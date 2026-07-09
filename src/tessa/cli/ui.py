"""Terminal rendering helpers built on Rich."""

from __future__ import annotations

from collections.abc import Iterator

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from tessa import __version__
from tessa.llm.types import ChatChunk

console = Console()

ACCENT = "medium_purple1"


def print_banner(model: str, project_kind: str | None = None) -> None:
    title = Text("TESSA", style=f"bold {ACCENT}")
    subtitle = Text.assemble(
        ("local AI coding agent  ", "dim"),
        (f"v{__version__}", "dim italic"),
    )
    body = Text.assemble(
        ("model  ", "dim"),
        (model, "bold"),
    )
    if project_kind:
        body.append_text(Text.assemble(("\nproject  ", "dim"), (project_kind, "")))
    console.print(Panel(body, title=title, subtitle=subtitle, border_style=ACCENT, expand=False))
    console.print("[dim]Type your request, or /help for commands. Ctrl-D to exit.[/dim]\n")


def print_error(message: str) -> None:
    console.print(f"[bold red]error:[/bold red] {message}")


def print_info(message: str) -> None:
    console.print(f"[{ACCENT}]•[/{ACCENT}] {message}")


def stream_response(chunks: Iterator[ChatChunk]) -> tuple[str, dict]:
    """Render a streaming reply as live-updating Markdown.

    While a thinking model reasons, the last few lines of its thinking are
    shown dimmed; they collapse away once the actual answer starts.
    Returns the full response text and the generation stats from the
    final chunk.
    """
    buffer: list[str] = []
    thinking: list[str] = []
    stats: dict = {}
    with Live(console=console, refresh_per_second=12, vertical_overflow="visible") as live:
        for chunk in chunks:
            if chunk.thinking and not buffer:
                thinking.append(chunk.thinking)
                live.update(_thinking_preview("".join(thinking)))
            if chunk.content:
                buffer.append(chunk.content)
                live.update(Markdown("".join(buffer)))
            if chunk.done:
                stats = chunk.stats
                if not buffer:  # model produced only thinking — show something
                    live.update(Markdown("".join(thinking)))
    return "".join(buffer) or "".join(thinking), stats


def _thinking_preview(text: str, max_lines: int = 4) -> Text:
    tail = [line for line in text.splitlines() if line.strip()][-max_lines:]
    preview = Text("thinking…\n", style=f"italic {ACCENT}")
    preview.append("\n".join(tail), style="dim")
    return preview


def format_stats(stats: dict) -> str | None:
    """Human-readable one-liner like '412 tokens · 9.3s · 44 tok/s'."""
    eval_count = stats.get("eval_count")
    total_ns = stats.get("total_duration")
    if not eval_count or not total_ns:
        return None
    seconds = total_ns / 1e9
    rate = eval_count / seconds if seconds else 0
    return f"{eval_count} tokens · {seconds:.1f}s · {rate:.0f} tok/s"
