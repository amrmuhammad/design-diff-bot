"""Command-line interface for design-diff-bot."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from .reporter import to_json, to_markdown
from .runner import find_kicad_files, kicad_cli_available, run_all_checks


@click.group()
@click.version_option(package_name="design-diff-bot")
def main() -> None:
    """design-diff-bot: CI/CD for KiCad designs."""


@main.command()
@click.argument(
    "directory",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("design-diff-report.json"),
    help="Path to write the JSON report.",
)
@click.option(
    "--markdown",
    "-m",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional path to write a Markdown report (for PR comments).",
)
@click.option(
    "--fail-on-violations",
    is_flag=True,
    default=False,
    help="Exit with code 1 if any violations are found.",
)
def check(
    directory: Path,
    output: Path,
    markdown: Path | None,
    fail_on_violations: bool,
) -> None:
    """Run ERC and DRC on all KiCad files in DIRECTORY."""
    click.echo(f"🔍 Scanning {directory} for KiCad files...")

    results = run_all_checks(directory)

    sch_count = len(results["schematics"])
    pcb_count = len(results["pcbs"])

    if sch_count == 0 and pcb_count == 0:
        click.echo("⚠️  No .kicad_sch or .kicad_pcb files found.")
        sys.exit(0)

    click.echo(f"   Found {sch_count} schematic(s) and {pcb_count} PCB(s).")

    if not results["kicad_cli_available"]:
        click.echo(
            "⚠️  kicad-cli is not installed. Reports will be empty. Install KiCad 8+ to run checks."
        )

    total = sum(e["violation_count"] for e in results["schematics"]) + sum(
        e["violation_count"] for e in results["pcbs"]
    )

    to_json(results, output)
    click.echo(f"📄 JSON report written to {output}")

    if markdown:
        md = to_markdown(results)
        markdown.write_text(md, encoding="utf-8")
        click.echo(f"📝 Markdown report written to {markdown}")

    if not results["kicad_cli_available"]:
        click.echo("ℹ️  Checks skipped (kicad-cli unavailable).")
        return

    if total == 0:
        click.echo("✅ No violations found.")
    else:
        click.echo(f"❌ {total} violation(s) found.")
        if fail_on_violations:
            sys.exit(1)


@main.command()
@click.argument(
    "directory",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
)
def scan(directory: Path) -> None:
    """List all KiCad files found in DIRECTORY."""
    files = find_kicad_files(directory)
    click.echo("Schematics:")
    for f in files["schematics"]:
        click.echo(f"  {f}")
    if not files["schematics"]:
        click.echo("  (none)")
    click.echo("PCBs:")
    for f in files["pcbs"]:
        click.echo(f"  {f}")
    if not files["pcbs"]:
        click.echo("  (none)")
    click.echo(f"kicad-cli available: {kicad_cli_available()}")


if __name__ == "__main__":
    main()
