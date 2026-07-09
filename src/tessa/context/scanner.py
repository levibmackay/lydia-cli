"""Repository scanning: file tree, language breakdown, important files.

This is the foundation of Tessa's repository intelligence (Milestone 2).
It is deliberately dependency-free and fast — a plain filesystem walk with
sensible ignore rules.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".tessa", "node_modules", "__pycache__",
    ".venv", "venv", "env", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "dist", "build", "target", "bin", "obj", ".idea", ".vscode",
    ".next", ".nuxt", "coverage", ".tox", "vendor",
}

LANGUAGE_BY_EXTENSION = {
    ".py": "Python", ".pyi": "Python",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".cs": "C#", ".fs": "F#",
    ".html": "HTML", ".css": "CSS", ".scss": "CSS",
    ".sql": "SQL",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
    ".c": "C", ".h": "C", ".cpp": "C++", ".hpp": "C++",
    ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
    ".sh": "Shell", ".zsh": "Shell", ".bash": "Shell",
    ".md": "Markdown", ".rst": "Markdown",
    ".json": "JSON", ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
    ".ipynb": "Jupyter",
}

# Files that reveal what kind of project this is, in rough display order.
MANIFEST_FILES = (
    "pyproject.toml", "setup.py", "requirements.txt", "Pipfile",
    "package.json", "tsconfig.json",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
    "Dockerfile", "docker-compose.yml", "Makefile",
    "README.md", "README.rst", "README.txt",
)

# Counted for line totals but excluded from language percentages,
# mirroring how GitHub's linguist treats data/prose files.
NON_CODE_LANGUAGES = {"Markdown", "JSON", "YAML", "TOML", "Jupyter"}

_MAX_FILES = 20_000  # safety valve for pathological directories


@dataclass
class ProjectSummary:
    root: Path
    file_count: int = 0
    total_lines: int = 0
    languages: dict[str, float] = field(default_factory=dict)  # name -> percent
    manifest_files: list[str] = field(default_factory=list)
    largest_source_files: list[tuple[str, int]] = field(default_factory=list)  # (path, lines)

    @property
    def project_kind(self) -> str:
        """A short human guess at the project type, from manifests + languages."""
        kinds = []
        manifests = set(self.manifest_files)
        if manifests & {"pyproject.toml", "setup.py", "requirements.txt", "Pipfile"}:
            kinds.append("Python")
        if "package.json" in manifests:
            kinds.append("Node.js")
        if manifests & {"Cargo.toml"}:
            kinds.append("Rust")
        if manifests & {"go.mod"}:
            kinds.append("Go")
        if any(f.endswith((".csproj", ".sln")) for f in self.manifest_files):
            kinds.append(".NET")
        if not kinds and self.languages:
            kinds.append(max(self.languages, key=self.languages.get))
        return " + ".join(kinds) if kinds else "Unknown"


def _count_lines(path: Path) -> int:
    try:
        with path.open("rb") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def scan_project(root: Path) -> ProjectSummary:
    """Walk *root* and build a summary of what the project contains."""
    root = root.resolve()
    summary = ProjectSummary(root=root)
    lines_by_language: Counter[str] = Counter()
    source_files: list[tuple[str, int]] = []

    stack = [root]
    while stack and summary.file_count < _MAX_FILES:
        directory = stack.pop()
        try:
            entries = sorted(directory.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.name.startswith(".") and entry.name not in (".env.example",):
                if entry.is_dir():
                    continue
            if entry.is_dir():
                if entry.name not in IGNORED_DIRS and not entry.is_symlink():
                    stack.append(entry)
                continue
            summary.file_count += 1
            relative = str(entry.relative_to(root))
            if entry.name in MANIFEST_FILES or entry.suffix in (".csproj", ".sln"):
                summary.manifest_files.append(relative)
            language = LANGUAGE_BY_EXTENSION.get(entry.suffix.lower())
            if language is None:
                continue
            lines = _count_lines(entry)
            summary.total_lines += lines
            if language not in NON_CODE_LANGUAGES:
                lines_by_language[language] += lines
                source_files.append((relative, lines))

    total_code_lines = sum(lines_by_language.values())
    if total_code_lines:
        summary.languages = {
            lang: round(100 * count / total_code_lines, 1)
            for lang, count in lines_by_language.most_common()
        }
    summary.largest_source_files = sorted(source_files, key=lambda x: -x[1])[:10]
    summary.manifest_files.sort(key=lambda f: _manifest_rank(f))
    return summary


def _manifest_rank(relative_path: str) -> int:
    name = Path(relative_path).name
    try:
        return MANIFEST_FILES.index(name)
    except ValueError:
        return len(MANIFEST_FILES)
