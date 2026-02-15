from pydantic import BaseModel, Field
from typing import Any, Optional

class SummarizeRequest(BaseModel):
    text: Optional[str] = Field(default=None, description="Transcript text")
    youtube_url: Optional[str] = Field(default=None, description="YouTube URL (optional)")
    language: str = Field(default="en", description="en/ru/kk")
    summary_sentences: int = Field(default=7, ge=3, le=15, description="How many sentences in summary")

class AnalyzeRequest(BaseModel):
    text: Optional[str] = None
    youtube_url: Optional[str] = None
    language: str = "en"

class ApiResponse(BaseModel):
    ok: bool = True
    data: Any = None
