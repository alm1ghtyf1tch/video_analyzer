import re
from collections import Counter
from app.services.stopwords import get_stopwords

# words incl. Cyrillic/Kazakh letters + apostrophes + digits
_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүІі0-9']+")
_TS_ONLY_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*$")  # mm:ss or hh:mm:ss
_TS_PREFIX_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s+")   # timestamp + space


def _ts_to_seconds(h_or_m: int, m: int, s: int | None) -> int:
    if s is None:
        # mm:ss
        return h_or_m * 60 + m
    # hh:mm:ss
    return h_or_m * 3600 + m * 60 + s


def parse_timestamped_transcript(text: str) -> list[dict] | None:
    """
    Parses transcripts like:
      okay dear students
      0:04
      there is...
      0:06
      ...
    Returns items: [{text,start,duration}]
    duration is unknown -> 0.0
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    items: list[dict] = []
    current_start: int | None = None

    for line in lines:
        raw = line.strip()
        if not raw:
            continue

        m = _TS_ONLY_RE.match(raw)
        if m:
            a = int(m.group(1))
            b = int(m.group(2))
            c = int(m.group(3)) if m.group(3) else None
            current_start = _ts_to_seconds(a, b, c)
            continue

        # if line starts with timestamp prefix "0:06 text..."
        m2 = _TS_PREFIX_RE.match(raw)
        if m2:
            a = int(m2.group(1))
            b = int(m2.group(2))
            c = int(m2.group(3)) if m2.group(3) else None
            current_start = _ts_to_seconds(a, b, c)
            raw = _TS_PREFIX_RE.sub("", raw).strip()

        if current_start is not None:
            items.append({"text": raw, "start": float(current_start), "duration": 0.0})

    return items if len(items) >= 3 else None


def _normalize_transcript(text: str) -> str:
    """
    - removes standalone timestamp lines
    - removes timestamp prefixes
    - merges lines into paragraphs (single newline -> space)
    """
    text = text.replace("λ", "lambda")  # optional: helps physics transcripts
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    cleaned_lines: list[str] = []
    for line in lines:
        s = line.strip()
        if not s:
            cleaned_lines.append("")  # keep paragraph breaks
            continue

        if _TS_ONLY_RE.match(s):
            continue  # drop timestamp-only line

        s = _TS_PREFIX_RE.sub("", s).strip()
        cleaned_lines.append(s)

    # merge: single newlines become spaces; blank lines become paragraph breaks
    paragraphs: list[str] = []
    buf: list[str] = []
    for s in cleaned_lines:
        if s == "":
            if buf:
                paragraphs.append(" ".join(buf))
                buf = []
        else:
            buf.append(s)
    if buf:
        paragraphs.append(" ".join(buf))

    out = "\n\n".join(paragraphs)
    out = re.sub(r"[ \t]+", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def clean_text(text: str) -> str:
    return _normalize_transcript(text).strip()


def split_sentences(text: str) -> list[str]:
    """
    Better sentence splitting for transcripts:
    - Prefer punctuation boundaries
    - If punctuation is missing, fall back to word-count chunks
    """
    text = clean_text(text)
    if not text:
        return []

    # primary split by punctuation
    parts = re.split(r"(?<=[.!?])\s+", text)
    sents = [p.strip() for p in parts if p and p.strip()]

    # fallback: no punctuation -> chunk by ~22 words
    if len(sents) < 3:
        words = text.split()
        target = 22
        sents = []
        buf = []
        for w in words:
            buf.append(w)
            if len(buf) >= target:
                sents.append(" ".join(buf).strip())
                buf = []
        if buf:
            sents.append(" ".join(buf).strip())

    # drop tiny junk
    return [s for s in sents if len(s) >= 40]


def tokenize_words(text: str, language: str = "en") -> list[str]:
    sw = get_stopwords(language)
    words = [w.lower() for w in _WORD_RE.findall(text)]
    out = []
    for w in words:
        if w.isdigit():
            continue
        if w in sw:
            continue
        if len(w) <= 2:
            continue
        out.append(w)
    return out


def top_keywords(text: str, language: str = "en", k: int = 12) -> list[tuple[str, int]]:
    words = tokenize_words(text, language)
    return Counter(words).most_common(k)


def top_bigrams(text: str, language: str = "en", k: int = 10) -> list[tuple[str, int]]:
    words = tokenize_words(text, language)
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
    return Counter(bigrams).most_common(k)


def fmt_mmss(seconds: float) -> str:
    s = int(seconds)
    m = s // 60
    s = s % 60
    return f"{m:02d}:{s:02d}"
