---
name: alphaxiv-paper-lookup
description: Look up arXiv papers through alphaXiv and return a structured AI-generated overview plus the arXiv abstract. Use when the user provides an arXiv URL, alphaXiv URL, or paper id; asks to summarize/explain/analyze a paper; or wants a faster overview before reading the PDF.
---

# alphaXiv Paper Lookup

Use this skill to turn an arXiv identifier or URL into a fast, structured paper brief.
Prefer alphaXiv first because it often exposes an AI-generated overview that is faster to scan than the raw PDF. Fall back to arXiv when alphaXiv is missing, thin, or unavailable.

## Quick workflow

1. Normalize the input into a paper id.
   - Accept plain ids like `2401.12345` or `1706.03762v7`
   - Accept arXiv URLs like `https://arxiv.org/abs/2401.12345`
   - Accept alphaXiv URLs like `https://www.alphaxiv.org/overview/2401.12345`
2. Run the bundled script:
   - `python3 scripts/alphaxiv_lookup.py "<paper-or-url>" --format markdown`
   - Use `--format json` when you want structured fields for downstream processing.
3. Read the returned fields in this priority order:
   - `alphaxiv_report`
   - `alphaxiv_description`
   - `arxiv_abstract`
   - `source_used`, `alphaxiv_status`, `arxiv_status`, `notes`
4. Write the answer in a fixed structure:
   - Paper title
   - What problem it solves
   - Core idea / method
   - Key findings
   - Limitations / caveats
   - Whether it is worth reading in full
5. If the user asks for deeper analysis, use the extracted report + abstract to produce:
   - Method breakdown
   - Comparison to prior work
   - Practical implications
   - Open questions

## Output template

Use this template unless the user requests a different style:

- **Paper**: title + id
- **一句话结论**: what the paper claims in one sentence
- **解决什么问题**: task / pain point / gap
- **核心方法**: 3-5 bullets
- **关键结果**: benchmarks, ablations, or empirical takeaways
- **局限性**: assumptions, missing comparisons, scalability, data dependence
- **值不值得细读**:
  - 值得细读 / 值得略读 / 只看摘要即可
  - give one short reason

## Fallback rules

- If alphaXiv returns only a thin description, combine it with the arXiv abstract instead of pretending the overview is complete.
- If alphaXiv fetch fails or appears rate-limited, say so briefly and fall back to arXiv.
- If the user asks for exact equations, implementation details, or appendix-level nuance, warn that alphaXiv is only a shortcut and the PDF/source paper should still be checked.
- Do not invent missing benchmark numbers. If a metric is absent, say it is not surfaced in the retrieved overview.

## Good trigger examples

- “帮我总结这篇 arXiv：2401.12345”
- “看看这个论文讲了什么 https://arxiv.org/abs/2401.12345”
- “解释一下这篇 paper 的核心贡献”
- “这个 alphaXiv 链接值不值得读原文？”
- “先帮我快速过一遍这篇论文，再决定要不要看 PDF”

## Resource

### scripts/alphaxiv_lookup.py

Normalize input, fetch alphaXiv overview pages, extract embedded report/description fields when available, and fall back to the arXiv abstract.
