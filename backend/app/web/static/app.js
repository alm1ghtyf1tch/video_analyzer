const out = document.getElementById("output");
const reportEl = document.getElementById("report");

function getPayload() {
  const youtube_url = document.getElementById("youtubeUrl").value.trim();
  const language = document.getElementById("language").value;
  const text = document.getElementById("text").value;
  const k = parseInt(document.getElementById("k").value || "7", 10);

  const payload = { language };
  if (youtube_url) payload.youtube_url = youtube_url;
  if (text && text.trim()) payload.text = text;
  payload.summary_sentences = k;

  return payload;
}

async function postJSON(path, payload) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

function esc(s) {
  return (s || "").replace(/[&<>"']/g, (c) => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
  }[c]));
}

function renderChips(words) {
  if (!words || !words.length) return `<p class="muted">No keywords.</p>`;
  return `<div class="chips">${words.map(w => `<span class="chip">${esc(w.word || w)}</span>`).join("")}</div>`;
}

function renderOutline(outline) {
  const segs = outline?.segments || [];
  if (!segs.length) return `<p class="muted">No outline segments.</p>`;
  return segs.map(seg => `
    <div class="seg">
      <strong>${esc(seg.range)}</strong><br/>
      <small>${esc((seg.keywords || []).join(", "))}</small>
    </div>
  `).join("");
}

function buildSummarizeReport(data) {
  const summary = data.summary || {};
  const bullets = summary.summary_bullets || summary.selected_sentences || [];
  const keywords = summary.keywords || [];
  const outline = data.outline || {};

  return `
    <h3>Summary</h3>
    ${bullets.length ? `<ul>${bullets.map(b => `<li>${esc(b)}</li>`).join("")}</ul>` : `<p class="muted">No summary.</p>`}

    <h3>Keywords</h3>
    ${renderChips(keywords)}

    <h3>Outline</h3>
    ${renderOutline(outline)}

    <p class="muted">Source: ${esc(data.source || "unknown")}</p>
  `;
}

function buildAnalyzeReport(data) {
  const stats = data.stats || {};
  const keywords = data.keywords || [];
  const phrases = data.keyphrases || [];
  const questions = data.questions || [];
  const actions = data.action_items || [];
  const sentiment = data.sentiment || {};
  const formulas = data.formula_snippets || [];

  return `
    <h3>Stats</h3>
    <ul>
      <li>Words: ${esc(String(stats.word_count ?? ""))}</li>
      <li>Sentences: ${esc(String(stats.sentence_count ?? ""))}</li>
      <li>Reading time (min): ${esc(String(stats.reading_time_min ?? ""))}</li>
      <li>Timestamps detected: ${esc(String(stats.has_timestamps ?? ""))}</li>
    </ul>

    <h3>Keywords</h3>
    ${renderChips(keywords)}

    <h3>Keyphrases</h3>
    ${phrases.length ? `<ul>${phrases.map(p => `<li>${esc(p.phrase || "")}</li>`).join("")}</ul>` : `<p class="muted">No keyphrases.</p>`}

    <h3>Questions</h3>
    ${questions.length ? `<ul>${questions.map(q => `<li>${esc(q)}</li>`).join("")}</ul>` : `<p class="muted">No questions detected.</p>`}

    <h3>Action items</h3>
    ${actions.length ? `<ul>${actions.map(a => `<li>${esc(a)}</li>`).join("")}</ul>` : `<p class="muted">No action items detected.</p>`}

    <h3>Sentiment</h3>
    <p>${esc(sentiment.label || "neutral")} (score: ${esc(String(sentiment.score ?? 0))})</p>

    <h3>Formula snippets</h3>
    ${formulas.length ? `<ul>${formulas.map(f => `<li>${esc(f)}</li>`).join("")}</ul>` : `<p class="muted">No formulas detected.</p>`}
  `;
}

function setReport(html) {
  reportEl.innerHTML = html;
}

document.getElementById("btnSummarize").onclick = async () => {
  setReport(`<p class="muted">Summarizing...</p>`);
  try {
    const payload = getPayload();
    const res = await postJSON("/api/summarize", payload);
    setReport(buildSummarizeReport(res.data));
    out.textContent = JSON.stringify(res.data, null, 2);
  } catch (e) {
    setReport(`<p>Error: ${esc(e.message)}</p>`);
  }
};

document.getElementById("btnAnalyze").onclick = async () => {
  setReport(`<p class="muted">Analyzing...</p>`);
  try {
    const payload = getPayload();
    const res = await postJSON("/api/analyze", payload);
    setReport(buildAnalyzeReport(res.data));
    out.textContent = JSON.stringify(res.data, null, 2);
  } catch (e) {
    setReport(`<p>Error: ${esc(e.message)}</p>`);
  }
};

document.getElementById("btnFetch").onclick = async () => {
  setReport(`<p class="muted">Fetching captions...</p>`);
  try {
    const url = document.getElementById("youtubeUrl").value.trim();
    if (!url) throw new Error("Paste a YouTube URL first.");
    const res = await fetch(`/api/youtube-transcript?url=${encodeURIComponent(url)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Fetch failed");
    document.getElementById("text").value = data.data.text || "";
    setReport(`<p>Captions loaded into transcript box.</p>`);
    out.textContent = JSON.stringify(data.data, null, 2);
  } catch (e) {
    setReport(`<p>Error: ${esc(e.message)}</p>`);
  }
};

document.getElementById("btnShowJson").onclick = () => {
  out.style.display = (out.style.display === "none") ? "block" : "none";
};

document.getElementById("btnCopy").onclick = async () => {
  const text = reportEl.innerText || "";
  try {
    await navigator.clipboard.writeText(text);
    // minimal feedback
    setReport(reportEl.innerHTML + `<p class="muted">Copied.</p>`);
  } catch {
    // fallback: show JSON and let user copy manually
    out.style.display = "block";
  }
};
