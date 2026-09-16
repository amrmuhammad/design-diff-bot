"""Core engine: runs KiCad ERC/DRC and returns structured results."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    """A single ERC or DRC check result."""

    tool: str
    success: bool
    violations: list[dict[str, Any]] = field(default_factory=list)
    raw_output: str = ""
    error: str | None = None


def kicad_cli_available() -> bool:
    """Check if kicad-cli is installed and on PATH."""
    return shutil.which("kicad-cli") is not None


def _run_kicad_cli(args: list[str]) -> tuple[int, str, str]:
    """Run kicad-cli with the given args. Returns (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["kicad-cli", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 127, "", "kicad-cli not found on PATH."


def _parse_violations(stdout: str) -> list[dict[str, Any]]:
    """Parse violations from kicad-cli JSON output. Returns [] on parse error."""
    if not stdout.strip():
        return []
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        return data.get("violations", [])
    return []


def run_erc(schematic_file: Path) -> CheckResult:
    """Run ERC on a .kicad_sch file."""
    if not kicad_cli_available():
        return CheckResult(
            tool="erc",
            success=False,
            error="kicad-cli is not installed or not on PATH.",
        )

    returncode, stdout, stderr = _run_kicad_cli(
        [
            "sch",
            "erc",
            "--format",
            "json",
            "--severity-all",
            "--exit-code-violations",
            "--output",
            "-",
            str(schematic_file),
        ]
    )

    # kicad-cli exit codes: 0 = no violations, 5 = violations found
    if returncode in (0, 5):
        return CheckResult(
            tool="erc",
            success=(returncode == 0),
            violations=_parse_violations(stdout),
            raw_output=stdout,
        )

    return CheckResult(
        tool="erc",
        success=False,
        raw_output=stdout,
        error=stderr or f"kicad-cli exited with code {returncode}",
    )


def run_drc(pcb_file: Path) -> CheckResult:
    """Run DRC on a .kicad_pcb file."""
    if not kicad_cli_available():
        return CheckResult(
            tool="drc",
            success=False,
            error="kicad-cli is not installed or not on PATH.",
        )

    returncode, stdout, stderr = _run_kicad_cli(
        [
            "pcb",
            "drc",
            "--format",
            "json",
            "--severity-all",
            "--exit-code-violations",
            "--output",
            "-",
            str(pcb_file),
        ]
    )

    if returncode in (0, 5):
        return CheckResult(
            tool="drc",
            success=(returncode == 0),
            violations=_parse_violations(stdout),
            raw_output=stdout,
        )

    return CheckResult(
        tool="drc",
        success=False,
        raw_output=stdout,
        error=stderr or f"kicad-cli exited with code {returncode}",
    )


def find_kicad_files(directory: Path) -> dict[str, list[Path]]:
    """Find all .kicad_sch and .kicad_pcb files under a directory."""
    schematics = sorted(directory.rglob("*.kicad_sch"))
    pcbs = sorted(directory.rglob("*.kicad_pcb"))
    return {"schematics": schematics, "pcbs": pcbs}


def run_all_checks(directory: Path) -> dict[str, Any]:
    """Run ERC on all schematics and DRC on all PCBs in a directory."""
    files = find_kicad_files(directory)
    results: dict[str, Any] = {
        "directory": str(directory),
        "kicad_cli_available": kicad_cli_available(),
        "schematics": [],
        "pcbs": [],
    }

    for sch in files["schematics"]:
        result = run_erc(sch)
        results["schematics"].append(
            {
                "file": str(sch),
                "tool": result.tool,
                "success": result.success,
                "violation_count": len(result.violations),
                "violations": result.violations,
                "error": result.error,
            }
        )

    for pcb in files["pcbs"]:
        result = run_drc(pcb)
        results["pcbs"].append(
            {
                "file": str(pcb),
                "tool": result.tool,
                "success": result.success,
                "violation_count": len(result.violations),
                "violations": result.violations,
                "error": result.error,
            }
        )

    return results
