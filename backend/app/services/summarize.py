
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.models.transcript import TranscriptChunk
from app.models.summary import Summary


_SPLIT_SENT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[a-zA-Z0-9']+")


def _sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    # split on punctuation boundaries
    return [s.strip() for s in _SPLIT_SENT.split(text) if s.strip()]


def _tokenize(s: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(s)]


def _score_sentences(sents: list[str]) -> list[tuple[float, int]]:
    """
    Very small frequency-based scoring:
      - word frequency with log dampening (ok for short notes)
      - sentence length prior to avoid super short/noisy lines
    Returns list of (score, index) sorted later.
    """
    toks = [ _tokenize(s) for s in sents ]
    freq = Counter([w for ts in toks for w in ts])
    if not freq:
        return [(0.0, i) for i in range(len(sents))]

    scores: list[tuple[float,int]] = []
    for i, ts in enumerate(toks):
        if not ts:
            scores.append((0.0, i))
            continue
        raw = sum(math.log(1 + freq[w]) for w in ts)
        # light length prior
        prior = min(len(ts) / 12.0, 1.0)
        scores.append(((raw / len(ts)) * (0.75 + 0.25 * prior), i))
    return scores


def _make_bullets(summary_lines: Iterable[str]) -> str:
    return "\n".join(f"- {line}" for line in summary_lines)


def _style_wrap(text: str, style: str) -> str:
    """
    Style-aware post-processing.
    - 'student': bullets with 'Key points' header
    - 'professional': bullets with a short preface
    """
    if style == "professional":
        return "Summary (for meeting minutes):\n" + text
    # default student
    return "Key points for study:\n" + text


async def generate_summary(db: AsyncSession, session_id: str, style: str = "student") -> Summary:
    """
    Pull transcript for the session, run a simple extractive summarizer,
    and persist a Summary row.
    """
    # ensure session exists
    s_result = await db.execute(select(Session).where(Session.id == session_id))
    session: Session | None = s_result.scalar_one_or_none()
    if not session:
        raise ValueError("Session not found")

    # load transcript chunks (already ordered by seq when we saved)
    t_result = await db.execute(
        select(TranscriptChunk)
        .where(TranscriptChunk.session_id == session_id)
        .order_by(TranscriptChunk.seq.asc())
    )
    chunks = t_result.scalars().all()
    full_text = " ".join(c.text for c in chunks).strip()

    if not full_text:
        # create a placeholder summary so the UI has something
        content = _style_wrap("- No transcript text available.", style)
        summary = Summary(session_id=session_id, style=style, content=content)
        db.add(summary)
        await db.commit()
        await db.refresh(summary)
        return summary

    sents = _sentences(full_text)
    if not sents:
        content = _style_wrap("- (Empty transcript)", style)
        summary = Summary(session_id=session_id, style=style, content=content)
        db.add(summary)
        await db.commit()
        await db.refresh(summary)
        return summary

    # rank & keep top 5–8 (depending on length)
    scores = sorted(_score_sentences(sents), key=lambda x: x[0], reverse=True)
    keep_k = max(3, min(8, len(sents) // 3 or 3))
    top = sorted(scores[:keep_k], key=lambda x: x[1])  # restore original order
    bullets = _make_bullets([sents[i] for _, i in top])

    content = _style_wrap(bullets, style)
    summary = Summary(session_id=session_id, style=style, content=content)
    db.add(summary)
    await db.commit()
    await db.refresh(summary)
    return summary
