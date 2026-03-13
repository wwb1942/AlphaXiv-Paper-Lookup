# AlphaXiv-Paper-Lookup

![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![GitHub Release](https://img.shields.io/github/v/release/wwb1942/AlphaXiv-Paper-Lookup)
![CI](https://github.com/wwb1942/AlphaXiv-Paper-Lookup/actions/workflows/ci.yml/badge.svg)
![Repo Visibility](https://img.shields.io/badge/visibility-public-blue.svg)

An OpenClaw skill for turning an arXiv id, arXiv URL, or alphaXiv URL into a fast structured paper brief.

It is designed for the workflow of **“give me a paper id or link, and tell me quickly whether it is worth reading in full.”**

## Quick links

- [Latest release](https://github.com/wwb1942/AlphaXiv-Paper-Lookup/releases/latest)
- [Download packaged skill](https://github.com/wwb1942/AlphaXiv-Paper-Lookup/releases/latest/download/alphaxiv-paper-lookup.skill)
- [Skill contract](./SKILL.md)
- [Changelog](./CHANGELOG.md)
- [Contributing guide](./CONTRIBUTING.md)
- [Security policy](./SECURITY.md)

## When to use

Use `AlphaXiv-Paper-Lookup` when you want to:

- summarize an arXiv paper quickly before opening the PDF
- turn an arXiv id or URL into a structured paper brief
- take advantage of alphaXiv overview pages when they are available
- fall back gracefully to the arXiv abstract when alphaXiv is thin, rate-limited, or unavailable
- speed up paper triage in research, reading, or agent workflows

## When not to use

This repository is **not** the best fit when you need:

- full PDF parsing as the primary workflow
- equation-level or appendix-level analysis without reading the source paper
- exact reproduction of benchmark tables from the PDF alone
- citation management across a paper library

In those cases, use this skill as a fast first-pass filter, then inspect the original paper.

## What it does

- normalize paper ids and URLs
- fetch alphaXiv overview pages when available
- extract embedded overview / report fields
- fall back to the arXiv abstract when alphaXiv is thin or unavailable
- return structured output in JSON, Markdown, verbose text, or a compact user-facing brief

## Quick examples

### Lookup by paper id

```bash
python3 scripts/alphaxiv_lookup.py '2603.07612' --format markdown
```

### Lookup by arXiv URL

```bash
python3 scripts/alphaxiv_lookup.py 'https://arxiv.org/abs/2603.07612' --format json
```

### Lookup by alphaXiv URL

```bash
python3 scripts/alphaxiv_lookup.py 'https://www.alphaxiv.org/overview/2603.07612' --format markdown
```

### Compact JSON for downstream automation

```bash
python3 scripts/alphaxiv_lookup.py '2603.07612' --format json-compact
```

### Plain-text detail view

```bash
python3 scripts/alphaxiv_lookup.py '2603.07612' --format text
```

### Compact user-facing brief

```bash
python3 scripts/alphaxiv_lookup.py '2603.07612' --format brief
```

### Increase timeout for slow upstreams

```bash
python3 scripts/alphaxiv_lookup.py '2603.07612' --format json --timeout 40
```

## Output fields

The JSON output may include:

- `paper_id`
- `resolved_alphaxiv_url`
- `arxiv_abs_url`
- `title`
- `authors`
- `source_used`
- `alphaxiv_status`
- `arxiv_status`
- `alphaxiv_description`
- `alphaxiv_report`
- `alphaxiv_report_key`
- `arxiv_abstract`
- `notes`

## `--format brief`

`--format brief` emits a deterministic, compact paper brief meant to be pasted directly to a user. It uses only retrieved fields and keeps working when alphaXiv is thin or unavailable by leaning on the arXiv fallback.

Structure:

- paper title + id
- one-line takeaway
- problem solved
- core method
- worth reading verdict
- source / confidence hint

## Repository layout

- `SKILL.md` — skill instructions and trigger guidance
- `scripts/alphaxiv_lookup.py` — lookup script
- `dist/alphaxiv-paper-lookup.skill` — packaged skill artifact
- `CHANGELOG.md` — notable release history
- `CONTRIBUTING.md` — contribution guide
- `SECURITY.md` — security reporting guidance
- `SUPPORT.md` — support and issue guidance

## Notes

- Repository display name is `AlphaXiv-Paper-Lookup`
- Technical skill slug remains `alphaxiv-paper-lookup`
- If alphaXiv fetch fails, is rate-limited, or has only a thin overview, the workflow falls back to arXiv as needed
- The JSON output now exposes `status`, `source_used`, `summary_source`, `best_summary`, `alphaxiv_status`, `arxiv_status`, `warnings`, and `errors` for easier downstream handling
- `--format brief` prefers the best retrieved summary, but can still produce a useful user-facing brief from the arXiv abstract alone
- AlphaXiv is treated as a shortcut, not a replacement for reading the full paper when exact details matter

## License

MIT
