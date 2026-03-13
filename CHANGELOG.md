# Changelog

All notable changes to this repository will be documented in this file.

## [Unreleased]

- Ongoing documentation and release polish.

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
