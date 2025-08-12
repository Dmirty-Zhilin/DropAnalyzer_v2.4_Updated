#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
domain_analyzer.py — Модуль анализа доменов для DropAnalyzer
Исправленная и упрощённая версия: асинхронный сбор метрик Wayback (CDX/Availability/Timemap)
и эвристическая классификация. Обрабатывает long-live домены.
"""

import asyncio
import json
import logging
import statistics
import os
from datetime import datetime
from typing import Dict, List, Set, Optional

import aiohttp

# ====== Конфигурация ======
CDX_API = "https://web.archive.org/cdx/search/cdx"
AVAIL_API = "https://archive.org/wayback/available"
TIMEMAP_URL = "http://web.archive.org/web/timemap/link/{url}"
REQUEST_TIMEOUT = 30
RETRY_DELAY = 2
RETRY_COUNT = 3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения списка long-live доменов
LONG_LIVE_DOMAINS: Set[str] = set()


def load_long_live_domains(file_path: Optional[str] = None) -> None:
    """Загружает список long-live доменов из файла.
    По умолчанию ищет long_live_domains.txt в папке backend и в корне проекта.
    """
    global LONG_LIVE_DOMAINS
    candidates = []
    if file_path:
        candidates.append(file_path)
    # путь рядом с этим модулем
    candidates.append(os.path.join(os.path.dirname(__file__), "long_live_domains.txt"))
    # путь выше (корень проекта)
    candidates.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "long_live_domains.txt"))

    for p in candidates:
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    LONG_LIVE_DOMAINS = {line.strip().lower() for line in f if line.strip()}
                logger.info(f"Loaded {len(LONG_LIVE_DOMAINS)} long-live domains from {p}")
                return
        except Exception as e:
            logger.warning(f"Cannot load long-live domains from {p}: {e}")

    LONG_LIVE_DOMAINS = set()
    logger.info("No long-live domains loaded.")


async def safe_request(session: aiohttp.ClientSession, method: str, url: str, **kwargs):
    """Универсальный безопасный запрос с ретраями. Возвращает JSON-объект или текст или None."""
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            async with session.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs) as resp:
                resp.raise_for_status()
                content_type = resp.headers.get("Content-Type", "")
                text_content = await resp.text()
                if "application/json" in content_type or kwargs.get("params", {}).get("output") == "json":
                    if not text_content.strip():
                        logger.warning(f"[{attempt}/{RETRY_COUNT}] Empty JSON response from {url}")
                        return None
                    try:
                        return json.loads(text_content)
                    except json.JSONDecodeError:
                        logger.warning(f"[{attempt}/{RETRY_COUNT}] JSON decode error for {url}")
                        return None
                return text_content
        except aiohttp.ClientResponseError as e:
            logger.warning(f"[{attempt}/{RETRY_COUNT}] HTTP error {getattr(e,'status',None)} for {url}: {e}")
            if attempt == RETRY_COUNT:
                return None
            if getattr(e, "status", None) == 429:
                await asyncio.sleep(RETRY_DELAY * attempt * 2)
            else:
                await asyncio.sleep(RETRY_DELAY * attempt)
        except asyncio.TimeoutError:
            logger.warning(f"[{attempt}/{RETRY_COUNT}] Timeout for {url}")
            if attempt == RETRY_COUNT:
                return None
        except Exception as e:
            logger.error(f"[{attempt}/{RETRY_COUNT}] Unexpected error for {url}: {e}")
            if attempt == RETRY_COUNT:
                return None
        if attempt < RETRY_COUNT:
            await asyncio.sleep(RETRY_DELAY * attempt)
    return None


def classify_by_wayback(info: Dict) -> Dict:
    """Эвристическая классификация на основе метрик Wayback."""
    snaps = int(info.get("total_snapshots") or 0)
    years = int(info.get("years_covered") or 0)
    try:
        avg_interval = float(info.get("avg_interval_days")) if info.get("avg_interval_days") not in (None, "") else float("inf")
    except Exception:
        avg_interval = float("inf")

    score = 0
    if snaps >= 100:
        score += 60
    elif snaps >= 20:
        score += 30

    if years >= 5:
        score += 30
    elif years >= 2:
        score += 15

    if avg_interval <= 365:
        score += 10

    score = max(0, min(100, int(score)))

    if score >= 80:
        category = "Recommended"
    elif score >= 40:
        category = "Medium"
    else:
        category = "Low Quality"

    info["quality_score"] = score
    info["category"] = category
    info["quality"] = category
    info["is_good"] = category in ("Recommended", "Medium")
    info["recommended"] = category == "Recommended"
    return info


async def analyze_single_domain(domain: str) -> Dict:
    """Асинхронный анализ одного домена: CDX, Availability, Timemap + классификация."""
    domain_norm = domain.strip().lower()
    info: Dict = {"domain": domain_norm}
    start = datetime.utcnow()

    async with aiohttp.ClientSession() as session:
        # Availability API
        try:
            avail_params = {"url": domain_norm}
            avail = await safe_request(session, "GET", AVAIL_API, params=avail_params)
            if avail and isinstance(avail, dict):
                closest = avail.get("archived_snapshots", {}).get("closest")
                info["has_snapshot"] = bool(closest and closest.get("available"))
                info["availability_ts"] = closest.get("timestamp") if closest else None
            else:
                info["has_snapshot"] = False
                info["availability_ts"] = None
        except Exception as e:
            logger.warning(f"Availability error for {domain_norm}: {e}")
            info["has_snapshot"] = False
            info["availability_ts"] = None

        # CDX API (пагинация батчами)
        records = []
        offset = 0
        limit = 1000
        base_cdx_params = {
            "url": domain_norm,
            "matchType": "exact",
            "output": "json",
            "fl": "timestamp,original,digest",
            "limit": limit
        }

        while True:
            cdx_params = {**base_cdx_params, "offset": offset}
            batch = await safe_request(session, "GET", CDX_API, params=cdx_params)
            if not batch:
                break
            # CDX returns array where first row can be header columns
            if isinstance(batch, list):
                if len(batch) >= 2 and isinstance(batch[0], list):
                    cols = batch[0]
                    for row in batch[1:]:
                        if isinstance(row, list) and len(row) == len(cols):
                            records.append(dict(zip(cols, row)))
                else:
                    # possibly list of dicts
                    for item in batch:
                        if isinstance(item, dict):
                            records.append(item)
            else:
                break

            if len(batch) < (limit + 1):  # header + items OR fewer items
                break
            offset += limit
            if offset > 50000:
                break

        info["total_snapshots"] = len(records)

        # Timemap (кол-во web/ ссылок)
        try:
            tm_text = await safe_request(session, "GET", TIMEMAP_URL.format(url=domain_norm))
            info["timemap_count"] = tm_text.count("web/") if tm_text and isinstance(tm_text, str) else 0
        except Exception:
            info["timemap_count"] = 0

        # Метрики снимков
        if records:
            try:
                times = [r.get("timestamp") for r in records if r.get("timestamp")]
                times = [t for t in times if isinstance(t, str) and len(t) >= 8]  # basic filter
                # prefer full timestamps of 14 chars
                dates = [datetime.strptime(ts, "%Y%m%d%H%M%S") for ts in times if len(ts) == 14]
                if dates:
                    dates = sorted(dates)
                    info["first_snapshot"] = dates[0].isoformat()
                    info["last_snapshot"] = dates[-1].isoformat()
                    gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))] if len(dates) > 1 else []
                    info["avg_interval_days"] = round(statistics.mean(gaps), 2) if gaps else 0
                    info["max_gap_days"] = max(gaps) if gaps else 0
                    years = sorted({d.year for d in dates})
                    info["years_covered"] = len(years)
                    info["snapshots_per_year"] = {y: sum(1 for d in dates if d.year == y) for y in years}
                    info["unique_versions"] = len({r.get("digest") for r in records if r.get("digest")})
                else:
                    for k in ("first_snapshot", "last_snapshot", "avg_interval_days", "max_gap_days",
                              "years_covered", "snapshots_per_year", "unique_versions"):
                        info[k] = None
            except Exception as e:
                logger.warning(f"Error processing metrics for {domain_norm}: {e}")
                for k in ("first_snapshot", "last_snapshot", "avg_interval_days", "max_gap_days",
                          "years_covered", "snapshots_per_year", "unique_versions"):
                    info[k] = None
        else:
            for k in ("first_snapshot", "last_snapshot", "avg_interval_days", "max_gap_days",
                      "years_covered", "snapshots_per_year", "unique_versions"):
                info[k] = None

    # Классификация по метрикам
    if any(info.get(k) for k in ("total_snapshots", "years_covered", "avg_interval_days")):
        info = classify_by_wayback(info)
    else:
        # fallback: long_live
        if domain_norm in LONG_LIVE_DOMAINS:
            info["quality"] = "Recommended"
            info["is_good"] = True
            info["recommended"] = True
            info["quality_score"] = 100
            info["category"] = "Recommended"
        else:
            info["quality"] = "Low Quality"
            info["is_good"] = False
            info["recommended"] = False
            info["quality_score"] = 0
            info["category"] = "Low Quality"

    # Ensure long-live override
    if domain_norm in LONG_LIVE_DOMAINS:
        info["quality_score"] = 100
        info["category"] = "Recommended"
        info["quality"] = "Recommended"
        info["is_good"] = True
        info["recommended"] = True

    info["analysis_time_sec"] = round((datetime.utcnow() - start).total_seconds(), 2)
    return info


def analyze_domain_sync(domain: str) -> Dict:
    """Синхронная обёртка для запуска асинхронного анализа."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # если loop уже запущен (например в некоторых средах), создаём новый временный
            new_loop = asyncio.new_event_loop()
            return new_loop.run_until_complete(analyze_single_domain(domain))
    except RuntimeError:
        pass

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(analyze_single_domain(domain))
    finally:
        try:
            loop.close()
        except Exception:
            pass


def analyze_domains_batch_sync(domains: List[str]) -> List[Dict]:
    """Синхронная обёртка для пакетного анализа доменов."""
    results: List[Dict] = []
    for d in domains:
        try:
            r = analyze_domain_sync(d)
            r["status"] = "completed"
            results.append(r)
        except Exception as e:
            logger.error(f"Error analyzing {d}: {e}")
            results.append({
                "domain": d,
                "status": "error",
                "error": str(e),
                "quality": "Low Quality",
                "is_good": False,
                "recommended": False,
                "quality_score": 0,
                "category": "Error"
            })
    return results


# Инициализация при импорте
load_long_live_domains()