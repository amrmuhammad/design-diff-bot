# design-diff-bot

CI/CD for KiCad designs. Runs ERC/DRC checks on every pull request and posts a structured design review comment.

## Badges

[![CI](https://github.com/amrmuhammad/design-diff-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/amrmuhammad/design-diff-bot/actions/workflows/ci.yml)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)

## What it does

- Automatic ERC/DRC checks on every PR
- Structured JSON report for machines, Markdown for humans
- PR comments updated in place (no comment spam)
- Runs locally too, same output

## Quick Start

Add this to `.github/workflows/design-review.yml`:

    name: Design Review
    on:
      pull_request:
        paths:
          - '**.kicad_sch'
          - '**.kicad_pcb'
    jobs:
      erc-drc:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: amrmuhammad/design-diff-bot@v0.1.0
            with:
              directory: .
              fail-on-violations: 'true'

## Inputs

- `directory` (default `.`) - where to scan for KiCad files
- `fail-on-violations` (default `'false'`) - fail if violations found
- `kicad-version` (default `'8.0'`) - KiCad version to install

## Outputs

- `report-path` - path to the JSON report
- `violation-count` - total violations found

## Local usage

    pip install design-diff-bot
    design-diff-bot check path/to/project
    design-diff-bot scan path/to/project

## Roadmap

- [x] ERC/DRC on pull requests
- [x] JSON and Markdown reports
- [ ] Design diff
- [ ] Hosted dashboard
- [ ] Custom rule packs

## License

MPL-2.0
