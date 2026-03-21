"""
Fetches daily news from NewsAPI + RSS feeds.
Focuses on: Toronto/Canada, global macro, AI/tech, behavioural science & spirituality.

Includes article-level dedup and diversity enforcement to prevent topic repetition.
"""
from __future__ import annotations

import logging
import random
import re
from datetime import datetime, timedelta, timezone
from typing import TypedDict

import xml.etree.ElementTree as ET
import requests

import config

log = logging.getLogger(__name__)

NEWSAPI_QUERIES = {
    "toronto_canada": [
        '"Toronto" AND (startup OR transit OR climate OR immigration OR tech)',
        '"Ontario economy" OR "Ontario housing" OR "Ontario policy" OR "Ontario energy"',
        '"Bank of Canada" OR "Canadian dollar" OR "Canada GDP" OR "Canada trade"',
    ],
    "global_macro": [
        '"emerging markets" OR "central bank" OR "sovereign debt" OR demographics',
        '"supply chain" OR sanctions OR tariff OR "trade deal"',
        'commodities OR currency OR "bond market" OR "fiscal policy"',
    ],
    "ai_tech": [
        '"artificial intelligence" OR "machine learning" OR "AI regulation"',
        'robotics OR biotech OR "quantum computing" OR semiconductor',
        'cybersecurity OR "open source" OR "space tech" OR "tech startup"',
    ],
    "behavioural_spirituality": [
        '"behavioural economics" OR "behavioral economics" OR "cognitive bias"',
        'mindfulness OR meditation OR "positive psychology" OR neuroscience',
        '"decision making" OR "nudge theory" OR wellbeing OR consciousness',
    ],
}

_STOP_WORDS = frozenset(
    "a an the and or but in on at to for of is it by with from as be was were "
    "are been has have had do does did will would could should may might shall "
    "this that these those its not no nor so if then than can new says after "
    "amid how why what when where who more about into over".split()
)


def _title_fingerprint(title: str) -> frozenset[str]:
    words = re.sub(r"[^a-z0-9\s]", "", title.lower()).split()
    return frozenset(w for w in words if w not in _STOP_WORDS and len(w) > 2)


def _titles_similar(fp1: frozenset[str], fp2: frozenset[str], threshold: float = 0.5) -> bool:
    if not fp1 or not fp2:
        return False
    overlap = len(fp1 & fp2)
    smaller = min(len(fp1), len(fp2))
    return (overlap / smaller) >= threshold if smaller > 0 else False


def _topic_cluster_key(title: str) -> str:
    fp = _title_fingerprint(title)
    top_words = sorted(fp)[:3]
    return " ".join(top_words) if top_words else title.lower()[:20]


class Article(TypedDict):
    title: str
    description: str
    url: str
    source: str
    published: str


def _fetch_newsapi(query: str, days_back: int = 2) -> list[Article]:
    from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime(
        "%Y-%m-%d"
    )
    params = {
        "q": query,
        "from": from_date,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": 8,
        "apiKey": config.NEWS_API_KEY,
    }
    try:
        resp = requests.get(
            f"{config.NEWS_API_BASE_URL}/everything", params=params, timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        articles: list[Article] = []
        for item in data.get("articles", []):
            if item.get("title") and item.get("description"):
                articles.append(
                    Article(
                        title=item["title"],
                        description=item.get("description", ""),
                        url=item.get("url", ""),
                        source=item.get("source", {}).get("name", "Unknown"),
                        published=item.get("publishedAt", ""),
                    )
                )
        return articles
    except Exception as exc:
        log.warning("NewsAPI error for query '%s': %s", query, exc)
        return []


def _fetch_newsapi_diverse(category: str, queries: list[str]) -> list[Article]:
    all_articles: list[Article] = []
    for q in queries:
        all_articles.extend(_fetch_newsapi(q))
    return _dedup_articles(all_articles)


def _parse_rss_xml(content: bytes, feed_url: str, max_items: int) -> list[Article]:
    articles: list[Article] = []
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        log.warning("XML parse error for %s: %s", feed_url, exc)
        return articles

    ns = {"atom": "http://www.w3.org/2005/Atom"}

    channel = root.find("channel")
    if channel is not None:
        feed_title = (channel.findtext("title") or feed_url).strip()
        for item in list(channel.findall("item"))[:max_items]:
            title = (item.findtext("title") or "").strip()
            desc = (item.findtext("description") or "").strip()[:500]
            link = (item.findtext("link") or "").strip()
            pub = (item.findtext("pubDate") or "").strip()
            if title:
                articles.append(Article(
                    title=title, description=desc, url=link,
                    source=feed_title, published=pub,
                ))
        return articles

    feed_title = (root.findtext("atom:title", namespaces=ns) or feed_url).strip()
    for entry in list(root.findall("atom:entry", namespaces=ns))[:max_items]:
        title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
        summary = (entry.findtext("atom:summary", namespaces=ns) or "").strip()[:500]
        link_el = entry.find("atom:link", namespaces=ns)
        link = (link_el.get("href", "") if link_el is not None else "").strip()
        pub = (entry.findtext("atom:published", namespaces=ns) or "").strip()
        if title:
            articles.append(Article(
                title=title, description=summary, url=link,
                source=feed_title, published=pub,
            ))
    return articles


def _fetch_rss_feeds(feeds: list[str], max_per_feed: int = 5) -> list[Article]:
    articles: list[Article] = []
    headers = {"User-Agent": "MindTheGap-PodcastBot/1.0"}

    for url in feeds:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            articles.extend(_parse_rss_xml(resp.content, url, max_per_feed))
        except Exception as exc:
            log.warning("RSS error for %s: %s", url, exc)

    return articles


def _dedup_articles(articles: list[Article]) -> list[Article]:
    seen_fps: list[frozenset[str]] = []
    unique: list[Article] = []
    for art in articles:
        fp = _title_fingerprint(art["title"])
        if any(_titles_similar(fp, s) for s in seen_fps):
            continue
        seen_fps.append(fp)
        unique.append(art)
    return unique


def _detect_saturated_keywords(covered_headlines: list[str], threshold: int = 3) -> set[str]:
    word_counts: dict[str, int] = {}
    for headline in covered_headlines:
        fp = _title_fingerprint(headline)
        for word in fp:
            word_counts[word] = word_counts.get(word, 0) + 1
    saturated = {w for w, c in word_counts.items() if c >= threshold}
    if saturated:
        log.info("Saturated keywords (appeared in %d+ headlines): %s", threshold, saturated)
    return saturated


def _remove_previously_covered(
    articles: list[Article],
    covered_headlines: list[str],
) -> tuple[list[Article], int | None]:
    if not covered_headlines:
        return articles, None

    covered_fps = [_title_fingerprint(h) for h in covered_headlines]
    saturated = _detect_saturated_keywords(covered_headlines)

    fresh: list[Article] = []
    stale: list[Article] = []
    saturated_articles: list[Article] = []
    for art in articles:
        fp = _title_fingerprint(art["title"])
        if any(_titles_similar(fp, cfp, threshold=0.4) for cfp in covered_fps):
            stale.append(art)
        elif saturated and len(fp & saturated) >= 2:
            saturated_articles.append(art)
        else:
            fresh.append(art)

    if stale:
        log.info("Filtered %d stale articles (direct headline match)", len(stale))
    if saturated_articles:
        log.info("Deprioritized %d articles containing saturated keywords", len(saturated_articles))

    depri_start = len(fresh) if saturated_articles else None
    return fresh + saturated_articles, depri_start


def _assign_cluster(art: Article, clusters: dict[str, list[Article]]) -> str:
    fp = _title_fingerprint(art["title"])
    for existing_key, members in clusters.items():
        rep_fp = _title_fingerprint(members[0]["title"])
        if _titles_similar(fp, rep_fp, threshold=0.35):
            return existing_key
    new_key = _topic_cluster_key(art["title"])
    return new_key


def _select_diverse(
    articles: list[Article],
    max_per_topic: int = 2,
    total: int = 8,
    deprioritized_start: int | None = None,
) -> list[Article]:
    priority_arts = articles[:deprioritized_start] if deprioritized_start else articles
    depri_arts = articles[deprioritized_start:] if deprioritized_start else []

    def _cluster_articles(arts: list[Article]) -> list[list[Article]]:
        clusters: dict[str, list[Article]] = {}
        for art in arts:
            key = _assign_cluster(art, clusters)
            clusters.setdefault(key, []).append(art)
        cl = list(clusters.values())
        random.shuffle(cl)
        return cl

    priority_clusters = _cluster_articles(priority_arts)
    depri_clusters = _cluster_articles(depri_arts)

    selected: list[Article] = []
    selected_fps: list[frozenset[str]] = []

    def _pick_from(cluster_list: list[list[Article]], round_num: int) -> None:
        for cluster in cluster_list:
            if len(selected) >= total:
                return
            if round_num < len(cluster):
                candidate = cluster[round_num]
                cfp = _title_fingerprint(candidate["title"])
                if not any(_titles_similar(cfp, sfp) for sfp in selected_fps):
                    selected.append(candidate)
                    selected_fps.append(cfp)

    for rnd in range(max_per_topic):
        _pick_from(priority_clusters, rnd)

    for rnd in range(max_per_topic):
        if len(selected) >= total:
            break
        _pick_from(depri_clusters, rnd)

    return selected


_depri_boundaries: dict[str, int | None] = {}


def fetch_daily_news(covered_headlines: list[str] | None = None) -> dict[str, list[Article]]:
    global _depri_boundaries
    _depri_boundaries = {}
    news: dict[str, list[Article]] = {}

    if config.NEWS_API_KEY:
        log.info("Fetching news from NewsAPI…")
        for category, queries in NEWSAPI_QUERIES.items():
            news[category] = _fetch_newsapi_diverse(category, queries)
    else:
        log.info("NEWS_API_KEY not set — using RSS feeds only.")
        for category in NEWSAPI_QUERIES:
            news[category] = []

    log.info("Fetching RSS feeds…")
    rss_raw = _fetch_rss_feeds(config.RSS_FEEDS)
    news["rss_general"] = _dedup_articles(rss_raw)

    if covered_headlines:
        for category in news:
            before = len(news[category])
            news[category], depri_start = _remove_previously_covered(
                news[category], covered_headlines
            )
            _depri_boundaries[category] = depri_start
            after = len(news[category])
            if before != after:
                log.info("  %s: %d → %d articles after stale filtering", category, before, after)

    total = sum(len(v) for v in news.values())
    log.info("Fetched %d unique articles across %d categories (after dedup).", total, len(news))
    return news


def summarise_for_prompt(news: dict[str, list[Article]]) -> str:
    lines: list[str] = []
    labels = {
        "toronto_canada": "TORONTO & CANADA",
        "global_macro": "GLOBAL MACRO ECONOMICS",
        "ai_tech": "AI & TECHNOLOGY",
        "behavioural_spirituality": "BEHAVIOURAL SCIENCE & SPIRITUALITY",
        "rss_general": "OTHER HEADLINES (diverse selection)",
    }
    global_fps: list[frozenset[str]] = []
    for key, articles in news.items():
        if not articles:
            continue
        depri_start = _depri_boundaries.get(key)
        selected = _select_diverse(articles, max_per_topic=2, total=8, deprioritized_start=depri_start)
        section_lines: list[str] = []
        for a in selected:
            fp = _title_fingerprint(a["title"])
            if any(_titles_similar(fp, gfp) for gfp in global_fps):
                continue
            global_fps.append(fp)
            section_lines.append(f"• [{a['source']}] {a['title']}")
            if a["description"]:
                section_lines.append(f"  {a['description'][:200]}")
        if section_lines:
            lines.append(f"\n=== {labels.get(key, key)} ===")
            lines.extend(section_lines)
    return "\n".join(lines)
