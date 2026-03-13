# Contributing

Thanks for taking a look at `AlphaXiv-Paper-Lookup`.

## Scope

This repository is a focused standalone export of an OpenClaw skill for fast paper lookup and summarization scaffolding.

Main contribution areas:

- alphaXiv extraction robustness
- arXiv fallback quality
- normalization edge cases for ids and URLs
- documentation and release polish

## Before opening a PR

1. Keep the technical skill slug as `alphaxiv-paper-lookup` unless there is a deliberate migration plan.
2. Prefer minimal, reviewable changes.
3. If you change script behavior, update examples or notes in the docs.
4. Do not commit secrets, tokens, or private datasets.

## Useful checks

```bash
python3 -m py_compile scripts/alphaxiv_lookup.py
python3 scripts/alphaxiv_lookup.py --help
```

## Pull requests

Please include:

- what changed
- why it changed
- how you verified it
- any fallback or compatibility risk
