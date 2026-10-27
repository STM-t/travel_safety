"""Адаптер GDELT DOC 2.0 — геополитика, протесты, забастовки."""
from __future__ import annotations

import logging

from ..config import get_settings
from ..models import GeopoliticalRisk
from .base import make_client, request_with_retry

logger = logging.getLogger("trisp.adapters.gdelt")

QUERY_KEYWORDS = "(protest OR strike OR unrest OR riot OR evacuation OR flood)"


async def fetch_geopolitical_risk(city: str, country: str) -> GeopoliticalRisk:
    """Новости за последние 30 дней по ключевым словам рисков."""
    settings = get_settings()
    risk = GeopoliticalRisk()

    query = f'{QUERY_KEYWORDS} "{city}"'
    params = {
        "query": query,
        "mode": "ArtList",
        "maxrecords": 75,
        "timespan": "30d",
        "format": "json",
        "sort": "DateDesc",
    }

    async with make_client() as client:
        resp = await request_with_retry(
            client, "GET", settings.gdelt_doc_url, params=params, retries=4, backoff=2.0
        )
        text = resp.text.strip()
        if not text or "{" not in text:
            return risk  # GDELT возвращает пустое/предупредительное тело, если статей нет
        try:
            data = text[text.index("{"):]  # иногда перед JSON идёт warning-строка
            import json
            payload = json.loads(data)
        except (ValueError, json.JSONDecodeError) as exc:
            logger.warning("GDELT parse error: %s", exc)
            return risk

    articles = payload.get("articles") or []
    risk.article_count = len(articles)

    tones = []
    for a in articles[:75]:
        try:
            tones.append(float(a.get("tone", 0)))
        except (TypeError, ValueError):
            pass
    if tones:
        risk.avg_tone = round(sum(tones) / len(tones), 2)

    seen_urls: set[str] = set()
    for a in articles:
        url = a.get("url", "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        risk.headlines.append({
            "title": a.get("title", "").strip(),
            "url": url,
            "date": a.get("seendate", ""),
            "source": a.get("domain", ""),
            "tone": a.get("tone", ""),
        })
        if len(risk.headlines) >= 5:
            break
    return risk
