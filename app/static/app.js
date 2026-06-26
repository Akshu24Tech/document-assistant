// Small vanilla front-end for the Document Assistant API.
// No build step, no framework — just fetch() against the /api routes.

const els = {
  fileInput: document.getElementById("file-input"),
  dropzone: document.getElementById("dropzone"),
  uploadStatus: document.getElementById("upload-status"),
  docList: document.getElementById("doc-list"),
  scope: document.getElementById("scope-select"),
  messages: document.getElementById("messages"),
  emptyState: document.getElementById("empty-state"),
  composer: document.getElementById("composer"),
  question: document.getElementById("question"),
  stream: document.getElementById("stream-toggle"),
  send: document.getElementById("send"),
};

// the chat history lives behind a session id the server hands back on the first ask
let sessionId = null;

// ---- documents ----------------------------------------------------------

async function loadDocuments() {
  const res = await fetch("/api/documents");
  if (!res.ok) return;
  const docs = await res.json();

  els.docList.innerHTML = "";
  els.scope.innerHTML = '<option value="">All documents</option>';

  for (const doc of docs) {
    const li = document.createElement("li");
    li.innerHTML = `<span class="doc-name">${escapeHtml(doc.filename)}</span>
                    <span class="doc-meta">${doc.chunks} chunks</span>`;
    els.docList.appendChild(li);

    const opt = document.createElement("option");
    opt.value = doc.document_id;
    opt.textContent = doc.filename;
    els.scope.appendChild(opt);
  }
}

async function uploadFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    return setUploadStatus("Only PDF files are supported.", "error");
  }

  setUploadStatus(`Uploading ${file.name}…`);
  const form = new FormData();
  form.append("file", file);

  try {
    const res = await fetch("/api/documents/upload", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Upload failed");
    setUploadStatus(`Indexed ${data.filename} — ${data.pages} pages, ${data.chunks} chunks.`, "ok");
    loadDocuments();
  } catch (err) {
    setUploadStatus(err.message, "error");
  }
}

function setUploadStatus(text, kind = "") {
  els.uploadStatus.textContent = text;
  els.uploadStatus.className = "upload-status" + (kind ? " " + kind : "");
}

els.fileInput.addEventListener("change", (e) => uploadFile(e.target.files[0]));

// drag-and-drop onto the upload box
["dragover", "dragenter"].forEach((evt) =>
  els.dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    els.dropzone.classList.add("drag");
  })
);
["dragleave", "drop"].forEach((evt) =>
  els.dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    els.dropzone.classList.remove("drag");
  })
);
els.dropzone.addEventListener("drop", (e) => uploadFile(e.dataTransfer.files[0]));

// ---- chat ---------------------------------------------------------------

els.composer.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = els.question.value.trim();
  if (question.length < 3) return;

  addMessage("user", question);
  els.question.value = "";
  setSending(true);

  const body = {
    question,
    session_id: sessionId,
    document_id: els.scope.value || null,
  };

  try {
    if (els.stream.checked) {
      await askStreaming(body);
    } else {
      await askOnce(body);
    }
  } catch (err) {
    addMessage("assistant", "⚠ " + err.message);
  } finally {
    setSending(false);
  }
});

async function askOnce(body) {
  const res = await fetch("/api/chat/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || data.detail || "Request failed");

  sessionId = data.session_id;
  addMessage("assistant", data.answer, data.sources);
}

async function askStreaming(body) {
  const res = await fetch("/api/chat/ask/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || data.detail || "Request failed");
  }

  sessionId = res.headers.get("X-Session-Id") || sessionId;

  const { bubble } = addMessage("assistant", "");
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let text = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    text += decoder.decode(value, { stream: true });
    bubble.textContent = text;
    scrollDown();
  }
}

// ---- rendering ----------------------------------------------------------

function addMessage(role, text, sources) {
  if (els.emptyState) els.emptyState.remove();

  const msg = document.createElement("div");
  msg.className = "msg " + role;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  msg.appendChild(bubble);

  if (sources && sources.length) {
    msg.appendChild(renderSources(sources));
  }

  els.messages.appendChild(msg);
  scrollDown();
  return { msg, bubble };
}

function renderSources(sources) {
  const wrap = document.createElement("div");
  wrap.className = "sources";
  wrap.innerHTML = '<div class="sources-title">Sources</div>';

  sources.forEach((s, i) => {
    const el = document.createElement("div");
    el.className = "source";
    el.innerHTML = `<div class="src-head">[${i + 1}] ${escapeHtml(s.filename)} · page ${s.page}</div>
                    <div class="src-snippet">${escapeHtml(s.snippet)}</div>`;
    wrap.appendChild(el);
  });
  return wrap;
}

function setSending(on) {
  els.send.disabled = on;
  els.send.textContent = on ? "…" : "Ask";
}

function scrollDown() {
  els.messages.scrollTop = els.messages.scrollHeight;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// initial load
loadDocuments();
