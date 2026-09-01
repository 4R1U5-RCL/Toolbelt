"""Split cleaned markdown into token-bounded chunks for an LLM context window.

The splitter is paragraph-aware and greedy: it packs whole blocks (separated by
blank lines) into a chunk until the next block would overflow ``max_tokens``,
then starts a new one. A single block bigger than the budget is hard-split by
characters so nothing is silently dropped. Token counts are the ~4-chars
estimate (KI-06), so leave headroom; ``overlap`` intentionally lets consecutive
chunks share a tail so a section straddling a boundary isn't lost.
"""

from __future__ import annotations

import re
from typing import List

from .model import Chunk
from .transform import estimate_tokens

_PARA_SPLIT = re.compile(r"\n{2,}")


def chunk_markdown(md: str, max_tokens: int = 1500, overlap: int = 0) -> List[Chunk]:
    if not md or not md.strip():
        return []
    if max_tokens < 1:
        raise ValueError("max_tokens must be >= 1")

    segments = [s.strip() for s in _PARA_SPLIT.split(md) if s.strip()]
    raw: List[str] = []
    current: List[str] = []
    current_tokens = 0

    for seg in segments:
        seg_tokens = estimate_tokens(seg)
        if seg_tokens > max_tokens:
            if current:
                raw.append("\n\n".join(current))
                current, current_tokens = [], 0
            raw.extend(_hard_split(seg, max_tokens))
            continue
        if current and current_tokens + seg_tokens > max_tokens:
            raw.append("\n\n".join(current))
            current, current_tokens = [], 0
        current.append(seg)
        current_tokens += seg_tokens

    if current:
        raw.append("\n\n".join(current))

    if overlap > 0:
        raw = _apply_overlap(raw, overlap)

    return [Chunk(index=i, text=text, tokens=estimate_tokens(text)) for i, text in enumerate(raw)]


def _hard_split(seg: str, max_tokens: int) -> List[str]:
    """Break an over-long block into <= max_tokens pieces by character count."""
    step = max_tokens * 4  # inverse of the 4-chars-per-token estimate
    return [seg[i : i + step] for i in range(0, len(seg), step)]


def _apply_overlap(chunks: List[str], overlap: int) -> List[str]:
    """Prefix each chunk (after the first) with the tail of the previous one."""
    tail_chars = overlap * 4
    out = [chunks[0]]
    for i in range(1, len(chunks)):
        tail = chunks[i - 1][-tail_chars:]
        out.append(tail + "\n\n" + chunks[i])
    return out
