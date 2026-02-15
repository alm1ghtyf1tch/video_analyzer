import re
from youtube_transcript_api import YouTubeTranscriptApi

def _extract_video_id(url: str) -> str:
    m = re.search(r"(v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    if not m:
        raise ValueError("Could not extract YouTube video id.")
    return m.group(2)

def fetch_youtube_transcript(url: str, languages: list[str] | None = None) -> list[dict]:
    """
    Returns list of items:
    [{ "text": str, "start": float, "duration": float }]
    """
    vid = _extract_video_id(url)
    languages = languages or ["en", "ru", "kk"]
    items = YouTubeTranscriptApi.get_transcript(vid, languages=languages)
    # sanitize to plain dicts
    out = []
    for it in items:
        out.append({
            "text": it.get("text", ""),
            "start": float(it.get("start", 0.0)),
            "duration": float(it.get("duration", 0.0)),
        })
    return out
