"""
Fetches social media reactions and discussions via web search (DuckDuckGo).

Covers Reddit, Twitter/X, HackerNews, forums, and other social platforms —
no API keys or credentials required.

For each news topic category, runs targeted searches to find recent social
discussions and reactions from real people.
"""
from __future__ import annotations

import logging
from typing import TypedDict

log = logging.getLogger(__name__)

SEARCH_QUERIES: dict[str, list[str]] = {
    "toronto_canada": [
        "Toronto housing market 2026 reddit discussion",
        "Canada interest rates Bank of Canada reaction people think",
        "Ontario economy cost of living opinions 2026",
    ],
    "global_macro": [
        "inflation recession 2026 reddit people saying",
        "Federal Reserve interest rates reaction discussion",
        "global economy trade tariffs what people think 2026",
    ],
    "ai_tech": [
        "artificial intelligence AI impact 2026 reddit discussion",
        "AI jobs tech layoffs reactions people saying",
        "ChatGPT AI regulation opinions hacker news reddit 2026",
    ],
    "behavioural_spirituality": [
        "behavioral economics real life examples people experience",
        "mindfulness productivity burnout discussion opinions",
    ],
}


class SocialReaction(TypedDict):
    source: str
    title: str
    snippet: str
    url: str


def fetch_social_reactions() -> dict[str, list[SocialReaction]]:
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            log.warning("ddgs package not installed. Skipping social reactions.")
            return {}

    results: dict[str, list[SocialReaction]] = {}

    for category, queries in SEARCH_QUERIES.items():
        reactions: list[SocialReaction] = []

        for query in queries:
            try:
                with DDGS() as ddgs:
                    search_results = list(ddgs.text(query, max_results=5, timelimit="w"))
                for item in search_results:
                    title = (item.get("title") or "").strip()
                    snippet = (item.get("body") or "").strip()
                    url = (item.get("href") or "").strip()

                    if not snippet or len(snippet) < 30:
                        continue

                    source = _extract_source(url)
                    reactions.append(
                        SocialReaction(
                            source=source,
                            title=title,
                            snippet=snippet[:400],
                            url=url,
                        )
                    )
            except Exception as exc:
                log.warning("Web search failed for query '%s': %s", query[:50], exc)

        if reactions:
            results[category] = reactions

    total = sum(len(v) for v in results.values())
    log.info("Fetched %d social reactions across %d categories via web search.", total, len(results))
    return results


def _extract_source(url: str) -> str:
    if not url:
        return "web"
    url_lower = url.lower()
    if "reddit.com" in url_lower:
        parts = url.split("/r/")
        if len(parts) > 1:
            sub = parts[1].split("/")[0]
            return f"Reddit r/{sub}"
        return "Reddit"
    if "twitter.com" in url_lower or "x.com" in url_lower:
        return "Twitter/X"
    if "news.ycombinator.com" in url_lower:
        return "HackerNews"
    if "quora.com" in url_lower:
        return "Quora"
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace("www.", "")
        return domain
    except Exception:
        return "web"


def summarise_social_for_prompt(reactions: dict[str, list[SocialReaction]]) -> str:
    if not reactions:
        return ""

    labels = {
        "toronto_canada": "TORONTO & CANADA",
        "global_macro": "GLOBAL MACRO",
        "ai_tech": "AI & TECHNOLOGY",
        "behavioural_spirituality": "BEHAVIOURAL SCIENCE",
    }

    lines: list[str] = [
        "\n\n========================================",
        "SOCIAL PULSE — What People Are Saying Online",
        "========================================",
        "These are snippets from real discussions found across Reddit, Twitter/X,",
        "HackerNews, forums, and other social platforms. Use them as 'voice of the",
        "people' color in the episode.",
        "When quoting, attribute naturally: 'One commenter online put it this way...'",
        "or 'Over on Reddit, the reaction was...' or 'As one person wrote on social media...'",
        "Do NOT fabricate any quotes — only use what appears below.\n",
    ]

    for category, category_reactions in reactions.items():
        if not category_reactions:
            continue
        lines.append(f"\n--- {labels.get(category, category)} ---")
        seen_titles: set[str] = set()
        for r in category_reactions[:6]:
            if r["title"] in seen_titles:
                continue
            seen_titles.add(r["title"])
            lines.append(f"\n[{r['source']}] {r['title']}")
            lines.append(f"  \"{r['snippet']}\"")

    return "\n".join(lines)
