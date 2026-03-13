# AlphaXiv-Paper-Lookup

An OpenClaw skill for turning an arXiv id, arXiv URL, or alphaXiv URL into a fast structured paper brief.

## What it does

- normalize paper ids and URLs
- fetch alphaXiv overview pages when available
- extract embedded overview / report fields
- fall back to the arXiv abstract when alphaXiv is thin or unavailable
- return structured output in JSON or Markdown

## Example

```bash
python3 scripts/alphaxiv_lookup.py '2603.07612' --format markdown
```

## Repository layout

- `SKILL.md` — skill instructions and trigger guidance
- `scripts/alphaxiv_lookup.py` — lookup script
- `dist/alphaxiv-paper-lookup.skill` — packaged skill artifact

## Notes

- Repository display name is `AlphaXiv-Paper-Lookup`
- Technical skill slug remains `alphaxiv-paper-lookup`
- If alphaXiv fetch fails, the workflow falls back to arXiv

## License

MIT
