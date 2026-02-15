# Video Analyzer (No AI)

Deterministic transcript summarizer + analyzer:

- Extractive summary (selects top sentences)
- Keywords, keyphrases (RAKE-like), outline segments
- Questions + action items heuristics
- Basic lexicon sentiment (no models)
- Optional: fetch YouTube captions (if available)

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
