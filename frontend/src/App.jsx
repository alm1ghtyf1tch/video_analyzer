import { useMemo, useState } from "react";
import LetterGlitch from "./components/Background";

const API_BASE = "http://127.0.0.1:8080"; // your FastAPI backend

export default function App() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [language, setLanguage] = useState("en");
  const [k, setK] = useState(7);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  const [reportHtml, setReportHtml] = useState(
    `<p style="opacity:.8">Run Summarize or Analyze to generate a readable report.</p>`
  );
  const [jsonVisible, setJsonVisible] = useState(false);
  const [rawJson, setRawJson] = useState("");

  const payload = useMemo(() => {
    const p = { language, summary_sentences: Number(k) || 7 };
    if (youtubeUrl.trim()) p.youtube_url = youtubeUrl.trim();
    if (text.trim()) p.text = text;
    return p;
  }, [youtubeUrl, language, k, text]);

  const esc = (s) =>
    String(s ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    }[c]));

  const chips = (arr) => {
    if (!arr?.length) return `<p style="opacity:.75">No keywords.</p>`;
    return `<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px;">
      ${arr.map((w) => `<span style="background:#0b1220;border:1px solid #223044;padding:6px 10px;border-radius:999px;font-size:12px;">${esc(w.word || w)}</span>`).join("")}
    </div>`;
  };

  const outline = (outlineObj) => {
    const segs = outlineObj?.segments || [];
    if (!segs.length) return `<p style="opacity:.75">No outline segments.</p>`;
    return segs.map(seg => `
      <div style="border:1px solid #223044;border-radius:10px;padding:10px;margin:10px 0;background:#0b1220;">
        <strong>${esc(seg.range)}</strong><br/>
        <small style="opacity:.8">${esc((seg.keywords || []).join(", "))}</small>
      </div>
    `).join("");
  };

  const buildSummaryReport = (data) => {
    const summary = data.summary || {};
    const bullets = summary.summary_bullets || summary.selected_sentences || [];
    const keywords = summary.keywords || [];
    const outl = data.outline || {};

    return `
      <h3 style="margin:14px 0 8px;">Summary</h3>
      ${bullets.length ? `<ul>${bullets.map(b => `<li>${esc(b)}</li>`).join("")}</ul>` : `<p style="opacity:.75">No summary.</p>`}

      <h3 style="margin:14px 0 8px;">Keywords</h3>
      ${chips(keywords)}

      <h3 style="margin:14px 0 8px;">Outline</h3>
      ${outline(outl)}

      <p style="opacity:.75;font-size:12px;margin-top:12px;">Source: ${esc(data.source || "unknown")}</p>
    `;
  };

  const buildAnalyzeReport = (data) => {
    const stats = data.stats || {};
    const keywords = data.keywords || [];
    const phrases = data.keyphrases || [];
    const questions = data.questions || [];
    const actions = data.action_items || [];
    const sentiment = data.sentiment || {};
    const formulas = data.formula_snippets || [];

    return `
      <h3 style="margin:14px 0 8px;">Stats</h3>
      <ul>
        <li>Words: ${esc(stats.word_count)}</li>
        <li>Sentences: ${esc(stats.sentence_count)}</li>
        <li>Reading time (min): ${esc(stats.reading_time_min)}</li>
        <li>Timestamps detected: ${esc(stats.has_timestamps)}</li>
      </ul>

      <h3 style="margin:14px 0 8px;">Keywords</h3>
      ${chips(keywords)}

      <h3 style="margin:14px 0 8px;">Keyphrases</h3>
      ${phrases.length ? `<ul>${phrases.map(p => `<li>${esc(p.phrase || p)}</li>`).join("")}</ul>` : `<p style="opacity:.75">No keyphrases.</p>`}

      <h3 style="margin:14px 0 8px;">Questions</h3>
      ${questions.length ? `<ul>${questions.map(q => `<li>${esc(q)}</li>`).join("")}</ul>` : `<p style="opacity:.75">No questions detected.</p>`}

      <h3 style="margin:14px 0 8px;">Action items</h3>
      ${actions.length ? `<ul>${actions.map(a => `<li>${esc(a)}</li>`).join("")}</ul>` : `<p style="opacity:.75">No action items detected.</p>`}

      <h3 style="margin:14px 0 8px;">Sentiment</h3>
      <p>${esc(sentiment.label || "neutral")} (score: ${esc(sentiment.score ?? 0)})</p>

      <h3 style="margin:14px 0 8px;">Formula snippets</h3>
      ${formulas.length ? `<ul>${formulas.map(f => `<li>${esc(f)}</li>`).join("")}</ul>` : `<p style="opacity:.75">No formulas detected.</p>`}
    `;
  };

  async function postJSON(path) {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Request failed");
    return data.data;
  }

  async function fetchCaptions() {
    const url = youtubeUrl.trim();
    if (!url) throw new Error("Paste a YouTube URL first.");
    const res = await fetch(`${API_BASE}/api/youtube-transcript?url=${encodeURIComponent(url)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Fetch failed");
    setText(data.data.text || "");
    setRawJson(JSON.stringify(data.data, null, 2));
    setReportHtml(`<p>Captions loaded into transcript box.</p>`);
  }

  async function runSummarize() {
    setLoading(true);
    try {
      const data = await postJSON("/api/summarize");
      setReportHtml(buildSummaryReport(data));
      setRawJson(JSON.stringify(data, null, 2));
    } finally {
      setLoading(false);
    }
  }

  async function runAnalyze() {
    setLoading(true);
    try {
      const data = await postJSON("/api/analyze");
      setReportHtml(buildAnalyzeReport(data));
      setRawJson(JSON.stringify(data, null, 2));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", position: "relative" }}>
      {/* Background */}
      <div
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 0,
          pointerEvents: "none", // key: background never blocks clicks
        }}
      >
        <LetterGlitch glitchSpeed={50} centerVignette={true} outerVignette={false} smooth={true} />
      </div>

      {/* Foreground UI */}
      <div
  style={{
    position: "relative",
    zIndex: 1,
    color: "#e8eefc",
    padding: 28,
    maxWidth: 920,
    margin: "0 auto",
  }}
>

        <h1 style={{ margin: "10px 0 18px" }}>Video Analyzer (No AI)</h1>

        <div style={{ background: "rgba(8,12,18,0.85)", border: "1px solid #223044", borderRadius: 14, padding: 18 }}>
          <label style={{ display: "block", fontSize: 12, opacity: 0.85 }}>YouTube URL (optional)</label>
          <input
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            style={{ width: "100%", padding: 10, margin: "6px 0 12px", borderRadius: 10, border: "1px solid #223044", background: "#0b1220", color: "white" }}
          />

          <label style={{ display: "block", fontSize: 12, opacity: 0.85 }}>Language</label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            style={{ width: "100%", padding: 10, margin: "6px 0 12px", borderRadius: 10, border: "1px solid #223044", background: "#0b1220", color: "white" }}
          >
            <option value="en">English</option>
            <option value="ru">Russian</option>
            <option value="kk">Kazakh</option>
          </select>

          <label style={{ display: "block", fontSize: 12, opacity: 0.85 }}>Summary sentences</label>
          <input
            type="number"
            min="3"
            max="15"
            value={k}
            onChange={(e) => setK(e.target.value)}
            style={{ width: "100%", padding: 10, margin: "6px 0 12px", borderRadius: 10, border: "1px solid #223044", background: "#0b1220", color: "white" }}
          />

          <label style={{ display: "block", fontSize: 12, opacity: 0.85 }}>Transcript text (paste here)</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={10}
            style={{ width: "100%", padding: 10, margin: "6px 0 12px", borderRadius: 10, border: "1px solid #223044", background: "#0b1220", color: "white", resize: "vertical" }}
          />

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button disabled={loading} onClick={runSummarize} style={btnStyle}>
              {loading ? "Working..." : "Summarize"}
            </button>
            <button disabled={loading} onClick={runAnalyze} style={btnStyle}>
              {loading ? "Working..." : "Analyze"}
            </button>
            <button disabled={loading} onClick={() => fetchCaptions().catch(e => setReportHtml(`<p>Error: ${esc(e.message)}</p>`))} style={btnStyle}>
              Fetch YouTube captions
            </button>
            <button onClick={() => setJsonVisible(v => !v)} style={btnGhostStyle}>
              Show/Hide JSON
            </button>
          </div>

          <p style={{ marginTop: 10, opacity: 0.75, fontSize: 12 }}>
            Backend: {API_BASE} (make sure FastAPI is running)
          </p>
        </div>

        <div style={{ marginTop: 18, background: "rgba(8,12,18,0.85)", border: "1px solid #223044", borderRadius: 14, padding: 18 }}>
          <h2 style={{ marginTop: 0 }}>Report</h2>
          <div dangerouslySetInnerHTML={{ __html: reportHtml }} />

          {jsonVisible && (
            <>
              <h3 style={{ marginTop: 16 }}>Raw JSON</h3>
              <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", background: "#0b1220", border: "1px solid #223044", padding: 12, borderRadius: 10 }}>
                {rawJson || "No JSON yet."}
              </pre>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

const btnStyle = {
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid #223044",
  background: "#1b4dff",
  color: "white",
  cursor: "pointer",
};

const btnGhostStyle = {
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid #223044",
  background: "#0b1220",
  color: "white",
  cursor: "pointer",
};
