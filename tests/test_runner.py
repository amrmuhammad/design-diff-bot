"""Tests for the design-diff-bot runner and reporter."""
from __future__ import annotations

from pathlib import Path

from design_diff_bot.reporter import to_markdown
from design_diff_bot.runner import (
    find_kicad_files,
    kicad_cli_available,
    run_all_checks,
)

# ---------- find_kicad_files ----------

def test_find_kicad_files_empty(tmp_path: Path) -> None:
    files = find_kicad_files(tmp_path)
    assert files["schematics"] == []
    assert files["pcbs"] == []


def test_find_kicad_files_finds_schematic(tmp_path: Path) -> None:
    (tmp_path / "board.kicad_sch").write_text("")
    files = find_kicad_files(tmp_path)
    assert len(files["schematics"]) == 1
    assert files["schematics"][0].name == "board.kicad_sch"


def test_find_kicad_files_finds_pcb(tmp_path: Path) -> None:
    (tmp_path / "board.kicad_pcb").write_text("")
    files = find_kicad_files(tmp_path)
    assert len(files["pcbs"]) == 1
    assert files["pcbs"][0].name == "board.kicad_pcb"


def test_find_kicad_files_finds_both(tmp_path: Path) -> None:
    (tmp_path / "a.kicad_sch").write_text("")
    (tmp_path / "b.kicad_pcb").write_text("")
    files = find_kicad_files(tmp_path)
    assert len(files["schematics"]) == 1
    assert len(files["pcbs"]) == 1


def test_find_kicad_files_recurses(tmp_path: Path) -> None:
    sub = tmp_path / "subdir" / "nested"
    sub.mkdir(parents=True)
    (sub / "deep.kicad_sch").write_text("")
    files = find_kicad_files(tmp_path)
    assert len(files["schematics"]) == 1


# ---------- run_all_checks ----------

def test_run_all_checks_no_files(tmp_path: Path) -> None:
    results = run_all_checks(tmp_path)
    assert results["schematics"] == []
    assert results["pcbs"] == []
    assert results["directory"] == str(tmp_path)
    assert "kicad_cli_available" in results


def test_run_all_checks_without_kicad_cli(tmp_path: Path) -> None:
    """If kicad-cli is missing, checks should not crash."""
    if kicad_cli_available():
        # Skip on machines that have KiCad installed
        return
    (tmp_path / "board.kicad_sch").write_text("")
    results = run_all_checks(tmp_path)
    assert len(results["schematics"]) == 1
    entry = results["schematics"][0]
    assert entry["violation_count"] == 0
    assert "kicad-cli is not installed" in (entry["error"] or "")


# ---------- to_markdown ----------

def test_to_markdown_clean() -> None:
    results = {
        "directory": ".",
        "kicad_cli_available": True,
        "schematics": [
            {
                "file": "board.kicad_sch",
                "tool": "erc",
                "success": True,
                "violation_count": 0,
                "violations": [],
                "error": None,
            }
        ],
        "pcbs": [],
    }
    md = to_markdown(results)
    assert "No violations found" in md
    assert "design-diff-bot" in md


def test_to_markdown_with_violations() -> None:
    results = {
        "directory": ".",
        "kicad_cli_available": True,
        "schematics": [
            {
                "file": "board.kicad_sch",
                "tool": "erc",
                "success": False,
                "violation_count": 1,
                "violations": [
                    {
                        "severity": "error",
                        "type": "pin_not_connected",
                        "description": "Pin not connected",
                        "items": [{"description": "U1 pin 5"}],
                    }
                ],
                "error": None,
            }
        ],
        "pcbs": [],
    }
    md = to_markdown(results)
    assert "Total violations:** 1" in md
    assert "pin_not_connected" in md
    assert "U1 pin 5" in md


def test_to_markdown_kicad_missing() -> None:
    results = {
        "directory": ".",
        "kicad_cli_available": False,
        "schematics": [],
        "pcbs": [],
    }
    md = to_markdown(results)
    assert "kicad-cli" in md
    assert "was not found" in md
