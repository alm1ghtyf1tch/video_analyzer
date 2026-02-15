import re
from collections import Counter
from app.services.text_utils import clean_text, split_sentences, tokenize_words, top_keywords, top_bigrams
from app.services.text_utils import parse_timestamped_transcript


_POS = {"good","great","excellent","love","like","awesome","clear","useful","helpful","amazing","success"}
_NEG = {"bad","terrible","hate","awful","confusing","unclear","useless","wrong","fail","problem","issue"}

_ACTION_HINTS_EN = ("should", "need to", "must", "let's", "we will", "do this", "make sure", "remember to")
_ACTION_HINTS_RU = ("нужно", "надо", "следует", "давайте", "мы будем", "сделайте", "убедитесь", "помните")
_ACTION_HINTS_KK = ("керек", "қажет", "жасайық", "біз", "ұмытпа", "есіңізде")

def _action_hints(lang: str):
    lang = (lang or "en").lower()
    if lang.startswith("ru"):
        return _ACTION_HINTS_RU
    if lang.startswith("kk") or lang.startswith("kz"):
        return _ACTION_HINTS_KK
    return _ACTION_HINTS_EN

def _sentiment_score(words: list[str]) -> int:
    score = 0
    for w in words:
        if w in _POS:
            score += 1
        if w in _NEG:
            score -= 1
    return score

def rake_phrases(text: str, language: str = "en", max_phrases: int = 12) -> list[dict]:
    """
    Simple RAKE-like phrase extraction:
    - Split on stopwords/punctuation
    - Score by word frequency/degree
    """
    words = tokenize_words(text, language)
    if not words:
        return []

    # Build candidate phrases by splitting original text on punctuation/newlines
    cleaned = clean_text(text.lower())
    parts = re.split(r"[.!?,:;\n()\[\]\"“”‘’]+", cleaned)

    sw = set()  # we already filtered in tokenize_words; here keep it simple
    candidates = []
    for p in parts:
        toks = [t for t in re.findall(r"[a-zа-яёәғқңөұүі0-9']+", p) if t and t not in sw]
        # keep only meaningful tokens (>=3 chars)
        toks = [t for t in toks if len(t) >= 3 and not t.isdigit()]
        if 2 <= len(toks) <= 6:
            candidates.append(toks)

    freq = Counter(words)
    degree = Counter()
    for cand in candidates:
        deg = len(cand) - 1
        for w in cand:
            degree[w] += deg

    scored = []
    for cand in candidates:
        score = 0.0
        for w in cand:
            score += (degree[w] + freq[w]) / max(1, freq[w])
        phrase = " ".join(cand)
        scored.append((phrase, score))

    seen = set()
    out = []
    for phrase, score in sorted(scored, key=lambda x: x[1], reverse=True):
        if phrase in seen:
            continue
        seen.add(phrase)
        out.append({"phrase": phrase, "score": round(score, 2)})
        if len(out) >= max_phrases:
            break
    return out

def analyze_transcript(text: str, language: str = "en", yt_items: list[dict] | None = None) -> dict:
    text = clean_text(text)
    sents = split_sentences(text)
    words = tokenize_words(text, language)

    word_count = len(re.findall(r"\S+", text))
    sentence_count = len(sents)
    reading_time_min = round(max(1, word_count) / 180.0, 2)  # ~180 wpm conservative

    kws = [{"word": w, "count": c} for (w, c) in top_keywords(text, language, k=12)]
    bigrams = [{"bigram": b, "count": c} for (b, c) in top_bigrams(text, language, k=10)]
    phrases = rake_phrases(text, language, max_phrases=12)

    questions = [s for s in sents if s.endswith("?")][:12]

    hints = _action_hints(language)
    action_items = []
    for s in sents:
        low = s.lower()
        if any(h in low for h in hints):
            action_items.append(s)
        if len(action_items) >= 12:
            break

    nums = re.findall(r"\b\d+(?:\.\d+)?\b", text)
    nums = nums[:20]

    sentiment = _sentiment_score(words)
    sentiment_label = "neutral"
    if sentiment >= 3:
        sentiment_label = "positive"
    elif sentiment <= -3:
        sentiment_label = "negative"

    if yt_items is None:
        yt_items = parse_timestamped_transcript(text)

    has_timestamps = bool(yt_items)


    return {
        "stats": {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "reading_time_min": reading_time_min,
            "has_timestamps": has_timestamps
        },
        "keywords": kws,
        "bigrams": bigrams,
        "keyphrases": phrases,
        "questions": questions,
        "action_items": action_items,
        "numeric_mentions": nums,
        "sentiment": {
            "score": sentiment,
            "label": sentiment_label
        }
    }
