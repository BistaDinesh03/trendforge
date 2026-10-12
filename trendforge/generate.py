"""Render an original project scaffold (never derived from other repos' code)."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from trendforge.config import TEMPLATES_DIR, Settings
from trendforge.models import DailyReport

MIT_LICENSE = """MIT License

Copyright (c) {year} {name} contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

SECURITY_MD = """# Security Policy

## Supported versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a vulnerability

Report security issues **privately** with GitHub Security Advisories for this
repository ("Report a vulnerability"). Do not open a public issue for an
exploitable vulnerability.

Include the affected component, steps to reproduce using local synthetic data
only, and the impact you observed. Never include real credentials, tokens, or
personal data. We will acknowledge the report when it is seen; details stay
private until a fix or mitigation is agreed.
"""

CONTRIBUTING_MD = """# Contributing

Thanks for helping improve {name}.

1. Fork the repository and create a focused feature branch.
2. Run `make setup`, then `make test` and `make lint` before pushing.
3. Keep pull requests small; describe the problem before the solution.
4. By contributing you agree your work is released under the MIT license.

Report security issues privately through GitHub Security Advisories, not in
public issues.
"""

SCAFFOLD_GITIGNORE = """__pycache__/
*.py[cod]
.venv/
venv/
.env
dist/
build/
*.egg-info/
.pytest_cache/
.ruff_cache/
.coverage
"""

SCAFFOLD_ENV_EXAMPLE = """# {name} config. Copy to .env and adjust; never commit real secrets.
LOG_LEVEL=info
HOST=127.0.0.1
PORT=8000
"""

SCAFFOLD_DEPENDABOT = """version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
"""

SCAFFOLD_MAKEFILE = """PYTHON ?= python3

.PHONY: setup run test lint

setup:
\t$(PYTHON) -m pip install -e ".[dev]"

run:
\t$(PYTHON) -m uvicorn {package}.main:app --host 127.0.0.1 --port 8000

test:
\t$(PYTHON) -m pytest -q

lint:
\t$(PYTHON) -m ruff check .
\t$(PYTHON) -m bandit -r src -lll
"""


def package_name(slug: str) -> str:
    """Turn a slug into a valid Python package name."""
    name = re.sub(r"[^a-z0-9_]+", "_", (slug or "").lower()).strip("_")
    if not name:
        name = "trendforge_project"
    if name[0].isdigit():
        name = f"pkg_{name}"
    return name


def _render(template_name: str, context: dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=("html", "xml"), default=False),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env.get_template(template_name).render(**context)


def _py_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _toml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _pyproject(slug: str, tagline: str) -> str:
    return f"""[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "{_toml_string(slug)}"
version = "0.1.0"
description = "{_toml_string(tagline)}"
readme = "README.md"
requires-python = ">=3.11"
license = {{ text = "MIT" }}
dependencies = [
    "fastapi>=0.111",
    "uvicorn>=0.30",
]

[project.optional-dependencies]
dev = ["pytest>=8.2", "ruff>=0.6", "bandit>=1.7.9"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "S", "UP"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]

[tool.ruff.lint.isort]
known-first-party = ["{_toml_string(package_name(slug))}"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
"""


def _dockerfile(package: str) -> str:
    return f"""FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

USER appuser

EXPOSE 8000
CMD ["uvicorn", "{package}.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def _service_main(name: str, slug: str) -> str:
    """Build the FastAPI entry point (short lines keep the scaffold ruff-clean)."""
    return (
        f'"""{_py_string(name)[1:-1]} service: original scaffold generated by TrendForge."""\n'
        "\n"
        "from fastapi import FastAPI\n"
        "\n"
        f'app = FastAPI(title={_py_string(name)}, version="0.1.0")\n'
        "\n"
        "\n"
        '@app.get("/health")\n'
        "def health() -> dict[str, str]:\n"
        '    """Liveness probe used by CI, Docker, and the Makefile."""\n'
        f'    return {{"service": {_py_string(slug)}, "status": "ok"}}\n'
    )


def _smoke_test(package: str, name: str) -> str:
    return (
        f'"""Smoke tests for {_py_string(name)[1:-1]}."""\n'
        "\n"
        "from fastapi.testclient import TestClient\n"
        "\n"
        f"from {package}.main import app\n"
        "\n"
        "\n"
        "def test_health_endpoint() -> None:\n"
        '    """The service must answer /health with a JSON status."""\n'
        "    client = TestClient(app)\n"
        '    response = client.get("/health")\n'
        "    assert response.status_code == 200\n"
        '    assert response.json()["status"] == "ok"\n'
    )


def generate_scaffold(settings: Settings, report: DailyReport) -> Path:
    """Write an original scaffold for the day's idea and return its directory."""
    idea = report.idea
    package = package_name(idea.slug)
    year = datetime.now(UTC).year
    out_dir: Path = settings.generated_dir / f"{report.date}-{idea.slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    readme = _render(
        "scaffold_readme.md.j2",
        {"idea": idea, "package": package, "date": report.date},
    )
    files: dict[str, str] = {
        "README.md": readme,
        "LICENSE": MIT_LICENSE.format(year=year, name=idea.name),
        "SECURITY.md": SECURITY_MD,
        "CONTRIBUTING.md": CONTRIBUTING_MD.format(name=idea.name),
        ".gitignore": SCAFFOLD_GITIGNORE,
        ".env.example": SCAFFOLD_ENV_EXAMPLE.format(name=idea.name),
        "pyproject.toml": _pyproject(idea.slug, idea.tagline),
        "Dockerfile": _dockerfile(package),
        "Makefile": SCAFFOLD_MAKEFILE.format(package=package),
        ".github/dependabot.yml": SCAFFOLD_DEPENDABOT,
        f"src/{package}/__init__.py": f'"""{idea.name} package."""\n\n__version__ = "0.1.0"\n',
        f"src/{package}/main.py": _service_main(idea.name, idea.slug),
        "tests/test_smoke.py": _smoke_test(package, idea.name),
    }
    for relative, content in files.items():
        target = out_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
    print(f"[trendforge] scaffold written: {out_dir} ({len(files)} files)")
    return out_dir
