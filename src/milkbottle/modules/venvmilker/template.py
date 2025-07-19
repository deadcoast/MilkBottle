"""Project template scaffolding for VENVmilker.

Currently supports a single built‑in template:
    * ``snakemake`` – a minimal but opinionated layout for Python projects
      that use *src* layout, pytest, and Snakemake workflows.

The template generator is deliberately lightweight – it writes files
programmatically rather than copying from a template directory so that the
entire module remains self‑contained and installable from a single wheel.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import Callable, Mapping, Sequence

from rich.console import Console

from milkbottle.modules.venvmilker.errors import CreateError, TemplateError

__all__: Sequence[str] = ["scaffold_project_template"]

# ---------------------------------------------------------------------------
# Template definitions (add more in future versions)
# ---------------------------------------------------------------------------


def _snakemake_files(project: str) -> Mapping[Path, str]:
    """Return mapping of *relative* file paths ➜ file contents for snakemake template."""
    return {
        Path(".gitignore"): dedent(
            """
            # Byte‑compiled / optimized / DLL files
            __pycache__/
            *.py[cod]
            *.so

            # Virtual environments
            .venv/
            venv/

            # Environment variables
            .env

            # PyInstaller
            dist/
            build/

            # macOS
            .DS_Store
            """
        ),
        Path("README.md"): f"# {project}\n\nGenerated with **VENVmilker**.\n",
        Path("LICENSE"): "MIT\n",
        Path("pyproject.toml"): dedent(
            f"""
            [project]
            name = "{project}"
            version = "0.1.0"
            description = "Generated with VENVmilker snakemake template"
            requires-python = ">=3.11"
            authors = [{{ name = "Your Name" }}]
            dependencies = []

            [tool.pytest.ini_options]
            addopts = "-ra"
            testpaths = ["tests"]
            """
        ),
        Path("src") / project / "__init__.py": "",
        Path("src")
        / project
        / "main.py": dedent(
            '''
            """Entry‑point CLI for the project."""
            import typer

            app = typer.Typer()


            @app.command()
            def hello(name: str = "world") -> None:  # noqa: D401
                """Say hello."""
                print(f"Hello, {name}!")


            if __name__ == "__main__":
                app()
            '''
        ),
        Path("tests") / "__init__.py": "",
        Path("tests")
        / "test_main.py": dedent(
            f'''
            """Basic sanity test for main CLI."""
            from importlib import metadata
            from pathlib import Path
            import subprocess
            import sys


            def test_cli_runs(tmp_path: Path) -> None:
                result = subprocess.run([sys.executable, "-m", "{project}", "hello"], capture_output=True, text=True)
                assert result.returncode == 0
            '''
        ),
        Path("Snakefile"): dedent(
            """
            # Example Snakemake workflow
            rule all:
                input: "results/hello.txt"

            rule hello:
                output: "results/hello.txt"
                shell:
                    "echo 'Hello from Snakemake!' > {output}"
            """
        ),
        Path("results") / ".gitkeep": "",  # keep dir in VCS
    }


# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------

TEMPLATE_REGISTRY: dict[str, Callable[[str], Mapping[Path, str]]] = {
    "snakemake": _snakemake_files,
}


def scaffold_project_template(
    root: Path, template: str, *, console: Console | None = None
) -> None:  # noqa: D401
    """Generate project files under *root* for *template*.

    Raises
    ------
    TemplateError
        If the template name is unknown.
    CreateError
        If any IO error occurs during file creation.
    """
    if template not in TEMPLATE_REGISTRY:
        available_templates = ", ".join(sorted(TEMPLATE_REGISTRY.keys()))
        raise TemplateError(
            f"Unknown template '{template}'. "
            f"Available templates: {available_templates}"
        )

    project_name = root.name.replace("-", "_")
    template_func = TEMPLATE_REGISTRY[template]
    files = template_func(project_name)

    for rel, content in files.items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            dest.write_text(content, encoding="utf-8")
        except OSError as exc:  # pragma: no cover
            raise CreateError(f"Failed to write template file {dest}: {exc}") from exc

    # Optionally notify user
    if console is not None:  # pragma: no branch
        console.print(f"[green]✓[/green] Project template '{template}' scaffolded.")
