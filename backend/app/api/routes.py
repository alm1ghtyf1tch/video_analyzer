from fastapi import APIRouter, HTTPException, Query
from app.api.models import SummarizeRequest, AnalyzeRequest, ApiResponse
from app.services.youtube import fetch_youtube_transcript
from app.services.summarizer import summarize_extractive, build_outline
from app.services.analyzer import analyze_transcript

router = APIRouter(prefix="/api")

@router.get("/health", response_model=ApiResponse)
def health():
    return ApiResponse(ok=True, data={"status": "ok"})

@router.get("/youtube-transcript", response_model=ApiResponse)
def youtube_transcript(url: str = Query(...)):
    items = fetch_youtube_transcript(url)
    joined = "\n".join([it["text"] for it in items if it.get("text")])
    return ApiResponse(ok=True, data={"items": items, "text": joined})

@router.post("/summarize", response_model=ApiResponse)
def summarize(req: SummarizeRequest):
    items = None
    text = (req.text or "").strip()

    if not text and req.youtube_url:
        items = fetch_youtube_transcript(req.youtube_url)
        text = "\n".join([it["text"] for it in items if it.get("text")]).strip()

    if not text:
        raise HTTPException(status_code=400, detail="Provide 'text' or 'youtube_url' with available captions.")

    summary = summarize_extractive(text=text, language=req.language, k=req.summary_sentences, yt_items=items)

    outline = build_outline(text=text, language=req.language, yt_items=items)

    return ApiResponse(ok=True, data={
        "summary": summary,
        "outline": outline,
        "source": "youtube_captions" if items else "pasted_text"
    })

@router.post("/analyze", response_model=ApiResponse)
def analyze(req: AnalyzeRequest):
    items = None
    text = (req.text or "").strip()

    if not text and req.youtube_url:
        items = fetch_youtube_transcript(req.youtube_url)
        text = "\n".join([it["text"] for it in items if it.get("text")]).strip()

    if not text:
        raise HTTPException(status_code=400, detail="Provide 'text' or 'youtube_url' with available captions.")

    result = analyze_transcript(text=text, language=req.language, yt_items=items)
    return ApiResponse(ok=True, data=result)
