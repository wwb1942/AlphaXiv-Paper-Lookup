# Changelog

All notable changes to this repository will be documented in this file.

## [Unreleased]

- Ongoing documentation and release polish.

## [v0.5.0] - 2026-03-13

### Added

- `--column COLUMN_NAME` support for reading paper ids / URLs from named columns in `.csv` and `.tsv` input files

### Changed

- plain-text `--input-file` behavior remains line-based and backward compatible
- structured CSV/TSV inputs now ignore blank rows, comment-only rows, and blank selected cells
- CSV/TSV files without `--column` now auto-select an input column only when it is unambiguous; otherwise the CLI fails with the available column names
- README, skill instructions, packaged artifact, and CI smoke coverage now document and verify structured file input handling

## [v0.4.1] - 2026-03-13

### Added

- `--input-file PATH` support for reading one paper id or URL per line, with blank lines and `#` comments ignored

### Changed

- combined positional arguments plus `--input-file` entries now reuse the existing single-item or batch rendering behavior automatically
- README and CI smoke coverage now document and verify file-driven batch input handling

## [v0.4.0] - 2026-03-13

### Added

- batch lookup mode by passing multiple paper ids / URLs in one command
- batch rendering for `markdown`, `text`, `brief`, and `brief-zh`
- batch JSON output as `{count, results}`
- batch `json-compact` output as JSONL for automation

### Changed

- single-item behavior remains backward compatible while multi-item invocations now render as grouped output

## [v0.3.2] - 2026-03-13

### Added

- `--format brief-zh` for a Chinese-labeled user-facing paper brief

### Changed

- `brief` and `brief-zh` now share the same evidence selection logic, with different presentation language only

## [v0.3.1] - 2026-03-13

### Added

- `--format brief` for a deterministic, compact, user-facing paper brief

### Changed

- documented the new brief mode and its arXiv-first fallback behavior when alphaXiv is thin or unavailable

## [v0.3.0] - 2026-03-13

### Added

- `--format text` for a plain-text brief
- `--format json-compact` for smaller machine-friendly payloads
- `status`, `summary_source`, `best_summary`, `warnings`, and `errors` output fields

### Changed

- prefer a cleaner arXiv abstract as `best_summary` when alphaXiv is only thin

### Fixed

- more precise alphaXiv status classification (`thin`, `no_report`, `rate_limited`, `not_found`, `upstream_error`, `http_error`, `network_error`)
- deduplicated candidate URL errors and cleaned alphaXiv overview prefixes
- kept HTML fragments out of summary fields

## [v0.2.0] - 2026-03-13

### Added

- `source_used`, `alphaxiv_status`, `arxiv_status`, and `resolved_arxiv_url` output fields
- `--timeout` CLI option for slower upstream responses

### Fixed

- arXiv fallback now uses cleaner metadata extraction for title, authors, and abstract
- alphaXiv candidate URLs are deduplicated to avoid duplicate error entries
- rate-limited alphaXiv failures are surfaced more clearly in notes and error output

## [v0.1.1] - 2026-03-13

### Added

- expanded README with usage guidance, examples, and output fields
- changelog, contributing guide, security policy, and support guide
- issue templates, PR template, and a minimal GitHub Actions CI workflow
- repository topics and homepage metadata

## [v0.1.0] - 2026-03-13

### Added

- Initial public standalone repository for the `alphaxiv-paper-lookup` OpenClaw skill
- `SKILL.md` skill contract and trigger guidance
- `scripts/alphaxiv_lookup.py` lookup script
- packaged release artifact: `dist/alphaxiv-paper-lookup.skill`
- MIT license
