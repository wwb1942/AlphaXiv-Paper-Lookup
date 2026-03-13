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


ALPHAXIV_STATUS_VALUES = {
    "available",
    "thin",
    "no_report",
    "rate_limited",
    "not_found",
    "upstream_error",
    "http_error",
    "network_error",
    "unavailable",
}


ARXIV_STATUS_VALUES = {"available", "unavailable", "unknown"}


SUMMARY_SOURCE_VALUES = {
    "alphaxiv_report",
    "alphaxiv_description",
    "arxiv_abstract",
    "none",
}


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


def clean_alpha_description(text: Optional[str]) -> str:
    text = clean_text(text)
    if not text:
        return ""
    text = re.sub(r"^View recent discussion\.?\s*", "", text, flags=re.I)
    text = re.sub(r"^Abstract:\s*", "", text, flags=re.I)
    text = re.sub(r"^Summary:\s*", "", text, flags=re.I)
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


def classify_http_error(err: urllib.error.HTTPError, body: str) -> Tuple[str, str]:
    lowered = body.lower()
    detail = f"HTTP {err.code}"
    if err.code == 404:
        return "not_found", detail + " (paper not found)"
    if err.code == 429 or "http 429" in body or "rate limit" in lowered or "api error (http 429)" in lowered:
        return "rate_limited", detail + " (rate limited upstream)"
    if 500 <= err.code < 600:
        return "upstream_error", detail + " (upstream service error)"
    return "http_error", detail


def fetch_with_classification(url: str, timeout: int = 25) -> Tuple[Optional[str], str, Optional[str]]:
    try:
        return fetch(url, timeout=timeout), "available", None
    except urllib.error.HTTPError as err:
        try:
            body = err.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        status, detail = classify_http_error(err, body)
        return None, status, f"{url}: {detail}"
    except Exception as err:
        return None, "network_error", f"{url}: {type(err).__name__}: {err}"


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
        except urllib.error.HTTPError as err:
            try:
                body = err.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            _, detail = classify_http_error(err, body)
            errors.append(f"{url}: {detail}")
        except Exception as err:
            errors.append(f"{url}: {type(err).__name__}: {err}")
    return {
        "title": "",
        "abstract": "",
        "authors": "",
        "url": candidates[0],
        "status": "unavailable",
        "errors": unique_preserve(errors),
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


def choose_best_summary(result: Dict[str, object]) -> Tuple[str, str]:
    if result.get("alphaxiv_report"):
        return "alphaxiv_report", str(result["alphaxiv_report"])
    if result.get("alphaxiv_status") == "available" and result.get("alphaxiv_description"):
        return "alphaxiv_description", str(result["alphaxiv_description"])
    if result.get("arxiv_abstract"):
        return "arxiv_abstract", str(result["arxiv_abstract"])
    if result.get("alphaxiv_description"):
        return "alphaxiv_description", str(result["alphaxiv_description"])
    return "none", ""


def summarize_status(title: str, best_summary: str) -> str:
    if title and best_summary:
        return "ok"
    if title or best_summary:
        return "partial"
    return "error"


def as_markdown(result: Dict[str, object]) -> str:
    lines = []
    lines.append(f"# {result.get('title') or result.get('paper_id')}")
    lines.append("")
    lines.append(f"- Paper ID: `{result.get('paper_id')}`")
    lines.append(f"- Status: `{result.get('status')}`")
    lines.append(f"- Source used: `{result.get('source_used')}`")
    lines.append(f"- Best summary: `{result.get('summary_source')}`")
    lines.append(f"- alphaXiv status: `{result.get('alphaxiv_status')}`")
    lines.append(f"- arXiv status: `{result.get('arxiv_status')}`")
    lines.append(f"- alphaXiv: {result.get('resolved_alphaxiv_url')}")
    lines.append(f"- arXiv: {result.get('resolved_arxiv_url') or result.get('arxiv_abs_url')}")
    if result.get("authors"):
        lines.append(f"- Authors: {result['authors']}")
    lines.append("")
    if result.get("best_summary"):
        lines.append("## Best available summary")
        lines.append("")
        lines.append(str(result["best_summary"]))
        lines.append("")
    if result.get("alphaxiv_report"):
        lines.append(f"## alphaXiv detailed report ({result.get('alphaxiv_report_key')})")
        lines.append("")
        lines.append(str(result["alphaxiv_report"]))
        lines.append("")
    elif result.get("alphaxiv_description"):
        lines.append("## alphaXiv quick overview")
        lines.append("")
        lines.append(str(result["alphaxiv_description"]))
        lines.append("")
    if result.get("arxiv_abstract") and result.get("summary_source") != "arxiv_abstract":
        lines.append("## arXiv abstract")
        lines.append("")
        lines.append(str(result["arxiv_abstract"]))
        lines.append("")
    warnings = result.get("warnings") or []
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")
    errors = result.get("errors") or []
    if errors:
        lines.append("## Errors")
        lines.append("")
        for error in errors:
            lines.append(f"- {error}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def as_text(result: Dict[str, object]) -> str:
    lines = []
    lines.append(f"Title: {result.get('title') or result.get('paper_id')}")
    lines.append(f"Paper ID: {result.get('paper_id')}")
    lines.append(f"Status: {result.get('status')}")
    lines.append(f"Source used: {result.get('source_used')}")
    lines.append(f"Best summary source: {result.get('summary_source')}")
    lines.append(f"alphaXiv status: {result.get('alphaxiv_status')}")
    lines.append(f"arXiv status: {result.get('arxiv_status')}")
    if result.get("authors"):
        lines.append(f"Authors: {result.get('authors')}")
    lines.append(f"alphaXiv URL: {result.get('resolved_alphaxiv_url')}")
    lines.append(f"arXiv URL: {result.get('resolved_arxiv_url') or result.get('arxiv_abs_url')}")
    if result.get("best_summary"):
        lines.append("")
        lines.append("Best available summary:")
        lines.append(str(result["best_summary"]))
    warnings = result.get("warnings") or []
    if warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in warnings:
            lines.append(f"- {warning}")
    errors = result.get("errors") or []
    if errors:
        lines.append("")
        lines.append("Errors:")
        for error in errors:
            lines.append(f"- {error}")
    return "\n".join(lines).strip() + "\n"


def compact_payload(result: Dict[str, object]) -> Dict[str, object]:
    return {
        "paper_id": result.get("paper_id"),
        "title": result.get("title"),
        "authors": result.get("authors"),
        "status": result.get("status"),
        "source_used": result.get("source_used"),
        "summary_source": result.get("summary_source"),
        "best_summary": result.get("best_summary"),
        "alphaxiv_status": result.get("alphaxiv_status"),
        "arxiv_status": result.get("arxiv_status"),
        "resolved_alphaxiv_url": result.get("resolved_alphaxiv_url"),
        "resolved_arxiv_url": result.get("resolved_arxiv_url"),
        "warnings": result.get("warnings", []),
        "errors": result.get("errors", []),
    }


def lookup(raw: str, timeout: int = 25) -> Dict[str, object]:
    urls = normalize_input(raw)
    candidates = unique_preserve([urls["alphaxiv_overview_url"], urls["alphaxiv_overview_url_no_version"]])
    alpha_page = ""
    alpha_url = candidates[0]
    alpha_errors: List[str] = []
    alpha_status = "unavailable"

    for url in candidates:
        page, fetch_status, error = fetch_with_classification(url, timeout=timeout)
        if page is not None:
            alpha_page = page
            alpha_url = url
            alpha_status = "available"
            break
        alpha_status = fetch_status
        if error:
            alpha_errors.append(error)

    alpha_errors = unique_preserve(alpha_errors)

    result: Dict[str, object] = {
        **urls,
        "resolved_alphaxiv_url": alpha_url,
        "resolved_arxiv_url": urls["arxiv_abs_url"],
        "status": "error",
        "source_used": "unknown",
        "summary_source": "none",
        "best_summary": "",
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
        "warnings": [],
        "errors": list(alpha_errors),
    }

    if alpha_page:
        meta_title = extract_meta(alpha_page, "og:title") or extract_meta(alpha_page, "twitter:title") or extract_title(alpha_page)
        meta_desc = extract_meta(alpha_page, "description") or extract_meta(alpha_page, "og:description") or extract_meta(alpha_page, "twitter:description")
        jsonld = extract_jsonld_article(alpha_page)
        reports = extract_reports(alpha_page)
        title = jsonld.get("headline") or meta_title.replace("| alphaXiv", "").strip()
        result["title"] = clean_text(title)
        result["alphaxiv_description"] = clean_alpha_description(meta_desc)
        result["authors"] = clean_text(jsonld.get("authors", ""))
        result["arxiv_abstract"] = clean_text(jsonld.get("abstract", ""))
        if reports:
            result["alphaxiv_report_key"] = reports[0][0]
            result["alphaxiv_report"] = reports[0][1]
            result["alphaxiv_status"] = "available"
        elif result["alphaxiv_description"]:
            result["alphaxiv_status"] = "thin"
            result["notes"].append("AlphaXiv page fetched, but only a short overview was available.")
        else:
            result["alphaxiv_status"] = "no_report"
            result["notes"].append("AlphaXiv page fetched, but no summary/report field was found.")
    else:
        if result["alphaxiv_status"] == "rate_limited":
            result["notes"].append("AlphaXiv appears rate-limited; falling back to arXiv abstract.")
        elif result["alphaxiv_status"] == "not_found":
            result["notes"].append("AlphaXiv overview page was not found; falling back to arXiv abstract.")
        elif result["alphaxiv_status"] == "upstream_error":
            result["notes"].append("AlphaXiv upstream returned a server error; falling back to arXiv abstract.")
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
            result["errors"] = unique_preserve(list(result["errors"]) + list(arxiv["errors"]))
            result["notes"].append("arXiv fallback had errors: " + "; ".join(arxiv["errors"]))
    else:
        result["arxiv_status"] = "available"

    result["source_used"] = infer_source_used(result)
    result["summary_source"], result["best_summary"] = choose_best_summary(result)
    result["status"] = summarize_status(str(result.get("title", "")), str(result.get("best_summary", "")))
    result["notes"] = unique_preserve(list(result["notes"]))
    result["warnings"] = list(result["notes"])
    result["errors"] = unique_preserve(list(result["errors"]))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Look up an arXiv paper via alphaXiv and extract structured overview fields.")
    parser.add_argument("paper", help="arXiv id, arXiv URL, or alphaXiv URL")
    parser.add_argument("--format", choices=["json", "json-compact", "markdown", "text"], default="json")
    parser.add_argument("--timeout", type=int, default=25, help="HTTP timeout in seconds (default: 25)")
    args = parser.parse_args()

    try:
        result = lookup(args.paper, timeout=args.timeout)
    except urllib.error.HTTPError as err:
        try:
            body = err.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        _, detail = classify_http_error(err, body)
        print(json.dumps({"error": f"HTTP {err.code}", "detail": detail, "input": args.paper}, ensure_ascii=False, indent=2))
        return 1
    except Exception as err:
        print(json.dumps({"error": type(err).__name__, "detail": str(err), "input": args.paper}, ensure_ascii=False, indent=2))
        return 1

    if args.format == "markdown":
        sys.stdout.write(as_markdown(result))
    elif args.format == "text":
        sys.stdout.write(as_text(result))
    elif args.format == "json-compact":
        print(json.dumps(compact_payload(result), ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
