
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
domain_analyzer.py — Модуль анализа доменов для DropAnalyzer

Интегрирует логику анализа доменов из way2_fixed_modified.py
для использования в Flask backend.
"""

import asyncio
import json
import logging
import statistics
from datetime import datetime
from typing import Dict, List, Set

import aiohttp
import pandas as pd

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

def load_long_live_domains(file_path: str = "long_live_domains.txt") -> None:
    """Загружает список long-live доменов из файла."""
    global LONG_LIVE_DOMAINS
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            LONG_LIVE_DOMAINS = {line.strip() for line in f if line.strip()}
        logger.info(f"Loaded {len(LONG_LIVE_DOMAINS)} long-live domains from {file_path}")
    except FileNotFoundError:
        logger.error(f"Long-live domains file not found: {file_path}")
        LONG_LIVE_DOMAINS = set()
    except Exception as e:
        logger.error(f"Error loading long-live domains: {e}")
        LONG_LIVE_DOMAINS = set()

async def safe_request(session: aiohttp.ClientSession, method: str, url: str, **kwargs):
    """Универсальный безопасный запрос с ретраями."""
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            async with session.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs) as resp:
                resp.raise_for_status()
                if kwargs.get("params", {}).get("output") == "json" or "application/json" in resp.headers.get("Content-Type", ""):
                    text_content = await resp.text()
                    if not text_content.strip():
                        logger.warning(f"[{attempt}/{RETRY_COUNT}] Empty JSON response from {url}")
                        return None
                    try:
                        return json.loads(text_content)
                    except json.JSONDecodeError as je:
                        logger.error(f"[{attempt}/{RETRY_COUNT}] JSON decode error for {url}: {je}")
                        if attempt == RETRY_COUNT:
                            return None
                else:
                    return await resp.text()
        except aiohttp.ClientResponseError as e:
            logger.warning(f"[{attempt}/{RETRY_COUNT}] HTTP error {e.status} for {url}: {e.message}")
            if e.status == 429:
                await asyncio.sleep(RETRY_DELAY * attempt * 2)
            elif e.status >= 500:
                await asyncio.sleep(RETRY_DELAY * attempt)
            elif attempt == RETRY_COUNT:
                logger.error(f"Failed to fetch {url} after {RETRY_COUNT} attempts due to HTTP {e.status}.")
                return None
        except asyncio.TimeoutError:
            logger.warning(f"[{attempt}/{RETRY_COUNT}] Timeout error for {url}")
            if attempt == RETRY_COUNT:
                logger.error(f"Failed to fetch {url} after {RETRY_COUNT} attempts due to timeout.")
                return None
        except Exception as e:
            logger.error(f"[{attempt}/{RETRY_COUNT}] Unexpected error for {url}: {e}")
            if attempt == RETRY_COUNT:
                return None
        if attempt < RETRY_COUNT:
            await asyncio.sleep(RETRY_DELAY * attempt)
    return None

async def analyze_single_domain(domain: str) -> Dict:
    """Анализирует один домен и возвращает результат."""
    info = {"domain": domain}
    start = datetime.utcnow()

    async with aiohttp.ClientSession() as session:
        # Availability API
        avail_params = {"url": domain}
        avail = await safe_request(session, "GET", AVAIL_API, params=avail_params)
        if avail and isinstance(avail, dict) and avail.get("archived_snapshots", {}).get("closest"):
            closest = avail["archived_snapshots"]["closest"]
            info["has_snapshot"] = bool(closest.get("available"))
            info["availability_ts"] = closest.get("timestamp")
        else:
            info["has_snapshot"] = False
            info["availability_ts"] = None

        # CDX API
        records = []
        offset = 0
        limit = 1000
        base_cdx_params = {
            "url": domain,
            "matchType": "exact",
            "output": "json",
            "fl": "timestamp,original,digest",
            "limit": limit
        }

        while True:
            cdx_params = {**base_cdx_params, "offset": offset}
            batch = await safe_request(session, "GET", CDX_API, params=cdx_params)
            
            if not batch or not isinstance(batch, list) or len(batch) < 1:
                break

            current_records = []
            if isinstance(batch[0], list):
                if len(batch) < 2:
                    break
                cols = batch[0]
                for row in batch[1:]:
                    if isinstance(row, list) and len(row) == len(cols):
                        records.append(dict(zip(cols, row)))
                        current_records.append(dict(zip(cols, row)))
            elif isinstance(batch[0], dict):
                for item in batch:
                    if isinstance(item, dict):
                        records.append(item)
                        current_records.append(item)
            else:
                break
            
            if len(current_records) < limit:
                break
            offset += limit
            if offset > 50000:
                break

        info["total_snapshots"] = len(records)

        # Timemap count
        tm_text = await safe_request(session, "GET", TIMEMAP_URL.format(url=domain))
        info["timemap_count"] = tm_text.count("web/") if tm_text and isinstance(tm_text, str) else 0

        # Метрики снимков
        if records:
            try:
                times = sorted([r["timestamp"] for r in records if "timestamp" in r and r["timestamp"] is not None])
                dates = [datetime.strptime(ts, "%Y%m%d%H%M%S") for ts in times if len(ts) == 14]
                if dates:
                    info["first_snapshot"] = dates[0].isoformat()
                    info["last_snapshot"] = dates[-1].isoformat()
                    gaps = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
                    info["avg_interval_days"] = round(statistics.mean(gaps), 2) if gaps else 0
                    info["max_gap_days"] = max(gaps) if gaps else 0
                    years = {d.year for d in dates}
                    info["years_covered"] = len(years)
                    info["snapshots_per_year"] = json.dumps({y: sum(1 for d in dates if d.year==y) for y in sorted(list(years))})
                    info["unique_versions"] = len({r["digest"] for r in records if "digest" in r})
                else:
                    for k in ("first_snapshot","last_snapshot","avg_interval_days",
                              "max_gap_days","years_covered","snapshots_per_year","unique_versions"):
                        info[k] = None
            except Exception as e:
                logger.error(f"Error processing snapshot metrics for {domain}: {e}")
                for k in ("first_snapshot","last_snapshot","avg_interval_days",
                          "max_gap_days","years_covered","snapshots_per_year","unique_versions"):
                    info[k] = None
        else:
            for k in ("first_snapshot","last_snapshot","avg_interval_days",
                      "max_gap_days","years_covered","snapshots_per_year","unique_versions"):
                info[k] = None

    # Определение качества на основе списка long-live доменов
    if domain in LONG_LIVE_DOMAINS:
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

    info["analysis_time_sec"] = round((datetime.utcnow() - start).total_seconds(), 2)
    return info

def analyze_domain_sync(domain: str) -> Dict:
    """Синхронная обертка для анализа домена."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(analyze_single_domain(domain))

def analyze_domains_batch_sync(domains: List[str]) -> List[Dict]:
    """Синхронная обертка для пакетного анализа доменов."""
    results = []
    for domain in domains:
        try:
            result = analyze_domain_sync(domain)
            result["status"] = "completed"
            results.append(result)
        except Exception as e:
            logger.error(f"Error analyzing domain {domain}: {e}")
            results.append({
                "domain": domain,
                "status": "error",
                "error": str(e),
                "quality": "Low Quality",
                "is_good": False,
                "recommended": False,
                "quality_score": 0,
                "category": "Error"
            })
    return results

# Инициализация при импорте модуля
load_long_live_domains()
