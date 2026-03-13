#!/usr/bin/env python3
import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"


def fetch(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def strip_html_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = text.replace("\r", "")
    text = re.sub(r"\\n", "\n", text)
    text = strip_html_tags(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def unique_preserve(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def extract_meta(html_text: str, name: str) -> str:
    patterns = [
        rf'<meta[^>]+name="{re.escape(name)}"[^>]+content="([^"]*)"',
        rf'<meta[^>]+property="{re.escape(name)}"[^>]+content="([^"]*)"',
    ]
    for pat in patterns:
        m = re.search(pat, html_text, re.I | re.S)
        if m:
            return clean_text(m.group(1))
    return ""


def extract_meta_many(html_text: str, name: str) -> List[str]:
    values: List[str] = []
    patterns = [
        rf'<meta[^>]+name="{re.escape(name)}"[^>]+content="([^"]*)"',
        rf'<meta[^>]+property="{re.escape(name)}"[^>]+content="([^"]*)"',
    ]
    for pat in patterns:
        for value in re.findall(pat, html_text, re.I | re.S):
            value = clean_text(value)
            if value:
                values.append(value)
    return unique_preserve(values)


def extract_title(html_text: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html_text, re.I | re.S)
    return clean_text(m.group(1) if m else "")


def extract_jsonld_article(html_text: str) -> Dict[str, str]:
    results: Dict[str, str] = {}
    for m in re.finditer(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html_text, re.I | re.S):
        raw = m.group(1).strip()
        try:
            data = json.loads(raw)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("@type") == "ScholarlyArticle":
                results["headline"] = clean_text(item.get("headline", ""))
                results["abstract"] = clean_text(item.get("abstract", ""))
                author = item.get("author")
                if isinstance(author, list):
                    names = []
                    for x in author:
                        if isinstance(x, dict) and x.get("name"):
                            names.append(clean_text(x["name"]))
                        elif isinstance(x, str):
                            names.append(clean_text(x))
                    results["authors"] = ", ".join([x for x in names if x])
                elif isinstance(author, dict) and author.get("name"):
                    results["authors"] = clean_text(author["name"])
                elif isinstance(author, str):
                    results["authors"] = clean_text(author)
                break
    return results


def extract_reports(html_text: str) -> List[Tuple[str, str]]:
    reports: List[Tuple[str, str]] = []
    for m in re.finditer(r'([A-Za-z]+Report):"((?:\\.|[^"\\])*)"', html_text, re.S):
        key, raw = m.group(1), m.group(2)
        try:
            text = json.loads('"' + raw + '"')
        except Exception:
            continue
        text = clean_text(text)
        if len(text) >= 200:
            reports.append((key, text))
    reports.sort(key=lambda x: len(x[1]), reverse=True)
    return reports


def describe_http_error(err: urllib.error.HTTPError) -> str:
    detail = f"HTTP {err.code}"
    try:
        body = err.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    lowered = body.lower()
    if err.code == 429 or "http 429" in body or "rate limit" in lowered or "api error (http 429)" in lowered:
        detail += " (rate limited upstream)"
    elif "api error" in lowered:
        detail += " (upstream API error)"
    return detail


def normalize_input(raw: str) -> Dict[str, str]:
    s = raw.strip()
    s = s.strip("<>")
    s = s.replace("https://alphaxiv.org/", "https://www.alphaxiv.org/")

    patterns = [
        r"arxiv\.org/(?:abs|pdf|html)/([^/?#]+)",
        r"alphaxiv\.org/(?:overview|paper|abs)/([^/?#]+)",
    ]
    for pat in patterns:
        m = re.search(pat, s, re.I)
        if m:
            paper_id = m.group(1)
            paper_id = re.sub(r"\.pdf$", "", paper_id, flags=re.I)
            return build_urls(paper_id, s)

    if re.fullmatch(r"[A-Za-z0-9._\-/]+", s):
        return build_urls(s, raw)

    raise ValueError(f"Could not parse arXiv/alphaXiv identifier from: {raw}")


def build_urls(paper_id: str, raw: str) -> Dict[str, str]:
    paper_id = paper_id.strip()
    paper_id = re.sub(r"\.pdf$", "", paper_id, flags=re.I)
    canonical_id = paper_id
    canonical_id_no_version = re.sub(r"v\d+$", "", canonical_id)
    return {
        "input": raw,
        "paper_id": canonical_id,
        "paper_id_no_version": canonical_id_no_version,
        "alphaxiv_overview_url": f"https://www.alphaxiv.org/overview/{canonical_id}",
        "alphaxiv_overview_url_no_version": f"https://www.alphaxiv.org/overview/{canonical_id_no_version}",
        "arxiv_abs_url": f"https://arxiv.org/abs/{canonical_id}",
        "arxiv_abs_url_no_version": f"https://arxiv.org/abs/{canonical_id_no_version}",
    }


def fetch_arxiv_abstract(urls: Dict[str, str], timeout: int = 25) -> Dict[str, object]:
    candidates = unique_preserve([urls["arxiv_abs_url"], urls["arxiv_abs_url_no_version"]])
    errors: List[str] = []
    for url in candidates:
        try:
            page = fetch(url, timeout=timeout)
            title = (
                extract_meta(page, "citation_title")
                or extract_meta(page, "og:title")
                or extract_meta(page, "twitter:title")
                or extract_title(page)
            )
            title = re.sub(r"^\[[^\]]+\]\s*", "", title).strip()
            authors = ", ".join(extract_meta_many(page, "citation_author"))
            abstract = (
                extract_meta(page, "citation_abstract")
                or extract_meta(page, "og:description")
                or extract_meta(page, "twitter:description")
            )
            if not abstract:
                m = re.search(r"Abstract:\s*(.*?)\s*(?:Comments:|Subjects:|Cite as:|$)", page, re.S | re.I)
                abstract = clean_text(m.group(1) if m else "")
            if title or abstract or authors:
                return {
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "url": url,
                    "status": "available",
                }
        except urllib.error.HTTPError as e:
            errors.append(f"{url}: {describe_http_error(e)}")
        except Exception as e:
            errors.append(f"{url}: {type(e).__name__}: {e}")
    return {
        "title": "",
        "abstract": "",
        "authors": "",
        "url": candidates[0],
        "status": "unavailable",
        "errors": errors,
    }


def infer_source_used(result: Dict[str, object]) -> str:
    has_alpha = bool(result.get("alphaxiv_report") or result.get("alphaxiv_description"))
    has_arxiv = bool(result.get("arxiv_abstract"))
    if has_alpha and has_arxiv:
        return "alphaxiv+arxiv"
    if has_alpha:
        return "alphaxiv"
    if has_arxiv:
        return "arxiv"
    return "unknown"


def lookup(raw: str, timeout: int = 25) -> Dict[str, object]:
    urls = normalize_input(raw)
    candidates = unique_preserve([urls["alphaxiv_overview_url"], urls["alphaxiv_overview_url_no_version"]])
    alpha_page = ""
    alpha_url = candidates[0]
    alpha_errors: List[str] = []
    alpha_status = "unavailable"

    for url in candidates:
        try:
            alpha_page = fetch(url, timeout=timeout)
            alpha_url = url
            alpha_status = "available"
            break
        except urllib.error.HTTPError as e:
            alpha_errors.append(f"{url}: {describe_http_error(e)}")
            if e.code == 429 or "rate limited" in alpha_errors[-1]:
                alpha_status = "rate_limited"
        except Exception as e:
            alpha_errors.append(f"{url}: {type(e).__name__}: {e}")

    result: Dict[str, object] = {
        **urls,
        "resolved_alphaxiv_url": alpha_url,
        "resolved_arxiv_url": urls["arxiv_abs_url"],
        "source_used": "unknown",
        "alphaxiv_available": bool(alpha_page),
        "alphaxiv_status": alpha_status,
        "alphaxiv_errors": alpha_errors,
        "arxiv_status": "unknown",
        "title": "",
        "alphaxiv_description": "",
        "alphaxiv_report": "",
        "alphaxiv_report_key": "",
        "authors": "",
        "arxiv_abstract": "",
        "notes": [],
    }

    if alpha_page:
        meta_title = extract_meta(alpha_page, "og:title") or extract_meta(alpha_page, "twitter:title") or extract_title(alpha_page)
        meta_desc = extract_meta(alpha_page, "description") or extract_meta(alpha_page, "og:description") or extract_meta(alpha_page, "twitter:description")
        jsonld = extract_jsonld_article(alpha_page)
        reports = extract_reports(alpha_page)
        title = jsonld.get("headline") or meta_title.replace("| alphaXiv", "").strip()
        result["title"] = clean_text(title)
        result["alphaxiv_description"] = clean_text(meta_desc)
        result["authors"] = clean_text(jsonld.get("authors", ""))
        result["arxiv_abstract"] = clean_text(jsonld.get("abstract", ""))
        if reports:
            result["alphaxiv_report_key"] = reports[0][0]
            result["alphaxiv_report"] = reports[0][1]
        else:
            result["notes"].append("AlphaXiv page fetched, but no embedded long-form report field was found.")
            if result["alphaxiv_description"]:
                result["alphaxiv_status"] = "thin"
    else:
        if result["alphaxiv_status"] == "rate_limited":
            result["notes"].append("AlphaXiv appears rate-limited or upstream-unavailable; falling back to arXiv abstract.")
        else:
            result["notes"].append("AlphaXiv overview fetch failed; falling back to arXiv abstract.")

    if not result["title"] or not result["arxiv_abstract"] or not result["authors"]:
        arxiv = fetch_arxiv_abstract(urls, timeout=timeout)
        result["resolved_arxiv_url"] = arxiv.get("url", urls["arxiv_abs_url"])
        result["arxiv_status"] = arxiv.get("status", "unknown")
        if not result["title"]:
            result["title"] = str(arxiv.get("title", ""))
        if not result["arxiv_abstract"]:
            result["arxiv_abstract"] = str(arxiv.get("abstract", ""))
        if not result["authors"]:
            result["authors"] = str(arxiv.get("authors", ""))
        if arxiv.get("errors"):
            result["notes"].append("arXiv fallback had errors: " + "; ".join(arxiv["errors"]))
    else:
        result["arxiv_status"] = "available"

    result["source_used"] = infer_source_used(result)
    return result


def as_markdown(result: Dict[str, object]) -> str:
    lines = []
    lines.append(f"# {result.get('title') or result.get('paper_id')}")
    lines.append("")
    lines.append(f"- Paper ID: `{result.get('paper_id')}`")
    lines.append(f"- Source used: `{result.get('source_used')}`")
    lines.append(f"- alphaXiv status: `{result.get('alphaxiv_status')}`")
    lines.append(f"- arXiv status: `{result.get('arxiv_status')}`")
    lines.append(f"- alphaXiv: {result.get('resolved_alphaxiv_url')}")
    lines.append(f"- arXiv: {result.get('resolved_arxiv_url') or result.get('arxiv_abs_url')}")
    if result.get("authors"):
        lines.append(f"- Authors: {result['authors']}")
    lines.append("")
    if result.get("alphaxiv_description"):
        lines.append("## alphaXiv quick overview")
        lines.append("")
        lines.append(str(result["alphaxiv_description"]))
        lines.append("")
    if result.get("alphaxiv_report"):
        lines.append(f"## alphaXiv detailed report ({result.get('alphaxiv_report_key')})")
        lines.append("")
        lines.append(str(result["alphaxiv_report"]))
        lines.append("")
    if result.get("arxiv_abstract"):
        lines.append("## arXiv abstract")
        lines.append("")
        lines.append(str(result["arxiv_abstract"]))
        lines.append("")
    notes = result.get("notes") or []
    if notes:
        lines.append("## Notes")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Look up an arXiv paper via alphaXiv and extract structured overview fields.")
    parser.add_argument("paper", help="arXiv id, arXiv URL, or alphaXiv URL")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--timeout", type=int, default=25, help="HTTP timeout in seconds (default: 25)")
    args = parser.parse_args()

    try:
        result = lookup(args.paper, timeout=args.timeout)
    except urllib.error.HTTPError as e:
        print(json.dumps({"error": f"HTTP {e.code}", "detail": describe_http_error(e), "input": args.paper}, ensure_ascii=False, indent=2))
        return 1
    except Exception as e:
        print(json.dumps({"error": type(e).__name__, "detail": str(e), "input": args.paper}, ensure_ascii=False, indent=2))
        return 1

    if args.format == "markdown":
        sys.stdout.write(as_markdown(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
