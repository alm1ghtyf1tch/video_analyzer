const out = document.getElementById("output");

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

document.getElementById("btnSummarize").onclick = async () => {
  out.textContent = "Summarizing...";
  try {
    const payload = getPayload();
    const data = await postJSON("/api/summarize", payload);
    out.textContent = JSON.stringify(data.data, null, 2);
  } catch (e) {
    out.textContent = `Error: ${e.message}`;
  }
};

document.getElementById("btnAnalyze").onclick = async () => {
  out.textContent = "Analyzing...";
  try {
    const payload = getPayload();
    const data = await postJSON("/api/analyze", payload);
    out.textContent = JSON.stringify(data.data, null, 2);
  } catch (e) {
    out.textContent = `Error: ${e.message}`;
  }
};

document.getElementById("btnFetch").onclick = async () => {
  out.textContent = "Fetching captions...";
  try {
    const url = document.getElementById("youtubeUrl").value.trim();
    if (!url) throw new Error("Paste a YouTube URL first.");
    const res = await fetch(`/api/youtube-transcript?url=${encodeURIComponent(url)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Fetch failed");
    document.getElementById("text").value = data.data.text || "";
    out.textContent = "Captions loaded into transcript box.";
  } catch (e) {
    out.textContent = `Error: ${e.message}`;
  }
};
