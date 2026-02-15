from collections import Counter
from app.services.text_utils import split_sentences, tokenize_words, top_keywords, fmt_mmss, parse_timestamped_transcript

def _sentence_scores(sentences: list[str], language: str) -> list[float]:
    all_words = []
    for s in sentences:
        all_words.extend(tokenize_words(s, language))
    freq = Counter(all_words)
    if not freq:
        return [0.0] * len(sentences)

    maxf = max(freq.values())
    scores = []
    for idx, s in enumerate(sentences):
        words = tokenize_words(s, language)
        if not words:
            scores.append(0.0)
            continue

        base = sum((freq[w] / maxf) for w in words) / (len(words) ** 0.65)

        # mild preference for earlier sentences
        pos_bonus = 1.0 + (0.12 * (1.0 - idx / max(1, len(sentences) - 1)))

        # prefer slightly longer / more informative sentences
        len_bonus = 1.0 + min(len(words), 35) / 120.0

        scores.append(base * pos_bonus * len_bonus)

    return scores

def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0

def summarize_extractive(text: str, language: str = "en", k: int = 7) -> dict:
    sents = split_sentences(text)
    if not sents:
        return {"summary_text": "", "selected_sentences": [], "keywords": []}

    scores = _sentence_scores(sents, language)

    # candidates by score desc
    cand_idx = sorted(range(len(sents)), key=lambda i: scores[i], reverse=True)

    selected_idx = []
    selected_sets: list[set[str]] = []

    for i in cand_idx:
        toks = set(tokenize_words(sents[i], language))
        # redundancy filter: skip if too similar to already selected
        if any(_jaccard(toks, prev) > 0.75 for prev in selected_sets):
            continue
        selected_idx.append(i)
        selected_sets.append(toks)
        if len(selected_idx) >= k:
            break

    selected_idx.sort()
    selected = [sents[i] for i in selected_idx]

    kw = [w for (w, c) in top_keywords(text, language, k=12)]

    return {
        "summary_text": " ".join(selected),
        "selected_sentences": selected,
        "keywords": kw
    }

def build_outline(text: str, language: str = "en", yt_items: list[dict] | None = None) -> dict:
    # if user pasted timestamps, parse them
    if yt_items is None:
        parsed = parse_timestamped_transcript(text)
        if parsed:
            yt_items = parsed

    if yt_items:
        window = 90.0
        segments = []
        cur = {"start": yt_items[0]["start"], "end": yt_items[0]["start"], "text": ""}

        for it in yt_items:
            t = it.get("start", 0.0)
            if t - cur["start"] > window and cur["text"].strip():
                segments.append(cur)
                cur = {"start": t, "end": t, "text": ""}

            cur["text"] += (" " if cur["text"] else "") + it.get("text", "")
            cur["end"] = max(cur["end"], t + it.get("duration", 0.0))

        if cur["text"].strip():
            segments.append(cur)

        out = []
        for seg in segments[:10]:
            kws = [w for (w, c) in top_keywords(seg["text"], language, k=6)]
            out.append({
                "range": f"{fmt_mmss(seg['start'])}–{fmt_mmss(seg['end'])}",
                "keywords": kws,
            })

        return {"mode": "timestamp_windows", "segments": out}

    # fallback: sentence blocks
    sents = split_sentences(text)
    if not sents:
        return {"mode": "empty", "segments": []}

    block = max(3, len(sents) // 6)
    out = []
    for i in range(0, len(sents), block):
        chunk = " ".join(sents[i:i + block])
        kws = [w for (w, c) in top_keywords(chunk, language, k=6)]
        out.append({"range": f"Part {len(out) + 1}", "keywords": kws})

    return {"mode": "sentence_blocks", "segments": out[:10]}
