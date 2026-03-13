# Changelog

All notable changes to this repository will be documented in this file.

## [Unreleased]

- Ongoing documentation and release polish.

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
