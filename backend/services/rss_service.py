from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import feedparser
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from models import Job, RankingRule


def _extract_entry_fields(entry: Any) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
    title = getattr(entry, "title", None) or ""
    url = getattr(entry, "link", None)
    description = getattr(entry, "summary", None) or getattr(entry, "description", None)
    company = getattr(entry, "author", None) or getattr(entry, "publisher", None)
    return title.strip(), (company.strip() if isinstance(company, str) else None), url, description


def _score_title_with_weights(title: str, weights: Dict[str, Any]) -> float:
    title_lower = title.lower()
    score = 0.0

    title_contains = weights.get("title_contains")
    if isinstance(title_contains, dict):
        for phrase, points in title_contains.items():
            if not isinstance(phrase, str):
                continue
            if phrase.lower() in title_lower:
                try:
                    score += float(points)
                except (TypeError, ValueError):
                    continue

    phrase = weights.get("phrase")
    points = weights.get("points")
    if isinstance(phrase, str):
        if phrase.lower() in title_lower:
            try:
                score += float(points)
            except (TypeError, ValueError):
                pass

    return score


def _apply_ranking_rules(db: Session, user_id: int, title: str) -> float:
    base_score = 0.0

    rules: List[RankingRule] = (
        db.query(RankingRule)
        .filter(and_(RankingRule.user_id == user_id, RankingRule.is_active == True))
        .order_by(RankingRule.id.asc())
        .all()
    )

    for rule in rules:
        weights = rule.weights if isinstance(rule.weights, dict) else {}
        base_score += _score_title_with_weights(title, weights)

    if "senior tpm" in title.lower():
        base_score += 30.0

    return base_score


def fetch_and_rank_jobs(
    db: Session,
    *,
    user_id: int,
    rss_url: str,
    rss_source_id: Optional[int] = None,
    limit: int = 25,
) -> List[Job]:
    parsed = feedparser.parse(rss_url)
    entries = list(getattr(parsed, "entries", []) or [])[: max(0, int(limit))]

    created: List[Job] = []
    now = datetime.utcnow()

    for entry in entries:
        title, company, url, description = _extract_entry_fields(entry)
        if not title:
            continue

        duplicate_query = db.query(Job).filter(Job.user_id == user_id)
        if url:
            duplicate_query = duplicate_query.filter(Job.url == url)
        else:
            duplicate_query = duplicate_query.filter(
                or_(
                    and_(Job.title == title, Job.company == company),
                    Job.title == title,
                )
            )

        existing = duplicate_query.first()
        if existing is not None:
            continue

        score = _apply_ranking_rules(db, user_id, title)

        job = Job(
            user_id=user_id,
            rss_source_id=rss_source_id,
            title=title,
            company=company,
            url=url,
            description=description,
            rank_score=score,
            date_added=now,
        )
        db.add(job)
        created.append(job)

    if created:
        db.commit()
        for job in created:
            db.refresh(job)

    return created

