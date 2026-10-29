"use strict";

// ---- state ---------------------------------------------------------------

// The access token arrives in the URL; keep it in sessionStorage so a reload still works.
const TOKEN = (() => {
  const fromUrl = new URLSearchParams(location.search).get("t");
  try {
    if (fromUrl) sessionStorage.setItem("token", fromUrl);
    return fromUrl || sessionStorage.getItem("token") || "";
  } catch {
    return fromUrl || "";
  }
})();
const COLORS = ["#2f6fde", "#d9480f", "#2b8a3e", "#ae3ec9", "#e67700", "#0b7285", "#c2255c", "#5f3dc4"];

const state = {
  sources: new Map(),   // id -> {id, name, page_count, locked, color}
  pages: [],            // [{uid, src, page}] in document order
  selected: new Set(),  // uids
  anchor: null,         // uid used as the start of shift-click ranges
  undo: [],
  redo: [],
  dirty: false,
  thumbWidth: 160,
};
let nextUid = 1;
let colorIndex = 0;

const $ = (id) => document.getElementById(id);
const grid = $("grid");
const cards = new Map(); // uid -> card element, reused across renders

// ---- API helpers ---------------------------------------------------------

async function api(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "X-Token": TOKEN, "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  const data = await res.json().catch(() => ({}));
  if (res.status === 501 && data.no_dialog) return { no_dialog: true };
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

function pageUrl(src, page, width) {
  return `/api/page/${src}/${page}?w=${width}&t=${encodeURIComponent(TOKEN)}`;
}

function toast(msg, isError = false) {
  const el = $("toast");
  el.textContent = msg;
  el.classList.toggle("error", isError);
  el.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (el.hidden = true), isError ? 6000 : 3000);
}

async function guarded(fn) {
  try {
    await fn();
  } catch (e) {
    toast(e.message, true);
  }
}

// ---- history -------------------------------------------------------------

function snapshot() {
  return state.pages.slice();
}

function commit(newPages) {
  state.undo.push(snapshot());
  if (state.undo.length > 200) state.undo.shift();
  state.redo = [];
  state.pages = newPages;
  state.dirty = true;
  render();
}

function undo() {
  if (!state.undo.length) return;
  state.redo.push(snapshot());
  state.pages = state.undo.pop();
  state.dirty = true;
  render();
}

function redo() {
  if (!state.redo.length) return;
  state.undo.push(snapshot());
  state.pages = state.redo.pop();
  state.dirty = true;
  render();
}

// ---- loading documents ---------------------------------------------------

async function addSources(sources, errors) {
  for (const err of errors || []) toast(err, true);
  const added = [];
  for (let src of sources) {
    if (src.locked) src = await askPassword(src);
    if (!src) continue;
    src.color = COLORS[colorIndex++ % COLORS.length];
    state.sources.set(src.id, src);
    for (let p = 0; p < src.page_count; p++) added.push({ uid: nextUid++, src: src.id, page: p });
  }
  return added;
}

function askPassword(src) {
  return new Promise((resolve) => {
    const dlg = $("pw-dialog");
    const input = $("pw-input");
    $("pw-label").textContent = `"${src.name}" is password protected.`;
    input.value = "";
    dlg.onclose = async () => {
      if (dlg.returnValue !== "ok") return resolve(null);
      try {
        resolve((await api("/api/unlock", { id: src.id, password: input.value })).source);
      } catch (e) {
        toast(e.message, true);
        resolve(await askPassword(src));
      }
    };
    dlg.showModal();
    input.focus();
  });
}

function resetDocument() {
  state.sources.clear();
  state.pages = [];
  state.selected.clear();
  state.anchor = null;
  state.undo = [];
  state.redo = [];
  state.dirty = false;
  cards.clear();
  grid.replaceChildren();
  colorIndex = 0;
}

async function openDocument() {
  if (state.dirty && !confirm("Discard unsaved changes and open another file?")) return;
  const res = await api("/api/open");
  if (res.no_dialog) return pickFiles(true);
  if (res.cancelled) return;
  await loadReplacing(res);
}

async function loadReplacing(res) {
  resetDocument();
  state.pages = await addSources(res.sources, res.errors);
  render();
}

async function appendDocuments() {
  const res = await api("/api/append");
  if (res.no_dialog) return pickFiles(false);
  if (res.cancelled) return;
  await loadAppending(res);
}

async function loadAppending(res) {
  const added = await addSources(res.sources, res.errors);
  if (!added.length) return render();
  commit(state.pages.concat(added));
  toast(`Appended ${added.length} page${added.length === 1 ? "" : "s"}.`);
}

// Fallback used when native dialogs are unavailable (e.g. no tkinter):
// the browser reads the files and posts them to the local server.
function pickFiles(replace) {
  const input = $("file-input");
  input.multiple = !replace;
  input.value = "";
  input.onchange = () => guarded(async () => {
    if (!input.files.length) return;
    const form = new FormData();
    for (const f of input.files) form.append("files", f);
    const res = await fetch(`/api/upload?replace=${replace ? 1 : 0}`, {
      method: "POST", headers: { "X-Token": TOKEN }, body: form,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Upload failed");
    await (replace ? loadReplacing(data) : loadAppending(data));
  });
  input.click();
}

async function saveDocument() {
  if (!state.pages.length) return;
  const first = state.sources.get(state.pages[0].src);
  const name = first ? first.name.replace(/\.pdf$/i, "") + "-edited.pdf" : "edited.pdf";
  const body = { name, pages: state.pages.map(({ src, page }) => ({ src, page })) };
  const res = await api("/api/save", body);
  if (res.cancelled) return;
  if (res.no_dialog) {
    const r = await fetch("/api/download", {
      method: "POST",
      headers: { "X-Token": TOKEN, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || "Save failed");
    const url = URL.createObjectURL(await r.blob());
    const a = Object.assign(document.createElement("a"), { href: url, download: name });
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
    state.dirty = false;
    return;
  }
  state.dirty = false;
  toast(`Saved to ${res.path}`);
}

// ---- editing operations --------------------------------------------------

function selectedItems() {
  return state.pages.filter((p) => state.selected.has(p.uid));
}

function deleteSelected() {
  if (!state.selected.size) return;
  const remaining = state.pages.filter((p) => !state.selected.has(p.uid));
  state.selected.clear();
  commit(remaining);
}

function moveSelected(toStart) {
  if (!state.selected.size) return;
  const moving = selectedItems();
  const rest = state.pages.filter((p) => !state.selected.has(p.uid));
  commit(toStart ? moving.concat(rest) : rest.concat(moving));
}

// Move the given uids so that they land before `beforeUid` (null = end).
function moveTo(uids, beforeUid) {
  const moving = state.pages.filter((p) => uids.has(p.uid));
  const rest = state.pages.filter((p) => !uids.has(p.uid));
  let idx = beforeUid == null ? rest.length : rest.findIndex((p) => p.uid === beforeUid);
  if (idx < 0) idx = rest.length;
  const result = rest.slice(0, idx).concat(moving, rest.slice(idx));
  if (result.every((p, i) => p === state.pages[i])) return; // dropped in place
  commit(result);
}

// ---- selection -----------------------------------------------------------

function onCardClick(e, uid) {
  if (e.shiftKey && state.anchor != null) {
    const a = state.pages.findIndex((p) => p.uid === state.anchor);
    const b = state.pages.findIndex((p) => p.uid === uid);
    if (!(e.ctrlKey || e.metaKey)) state.selected.clear();
    for (let i = Math.min(a, b); i <= Math.max(a, b); i++) state.selected.add(state.pages[i].uid);
  } else if (e.ctrlKey || e.metaKey) {
    if (state.selected.has(uid)) state.selected.delete(uid);
    else state.selected.add(uid);
    state.anchor = uid;
  } else {
    state.selected.clear();
    state.selected.add(uid);
    state.anchor = uid;
  }
  render();
}

// ---- drag and drop -------------------------------------------------------

let dragUids = null;
let dropMarker = null; // {el, after}

function clearDropMarker() {
  if (dropMarker) dropMarker.el.classList.remove("drop-before", "drop-after");
  dropMarker = null;
}

function onDragStart(e, uid) {
  if (!state.selected.has(uid)) {
    state.selected.clear();
    state.selected.add(uid);
    state.anchor = uid;
    render();
  }
  dragUids = new Set(state.selected);
  e.dataTransfer.effectAllowed = "move";
  e.dataTransfer.setData("text/plain", "pages");
  if (dragUids.size > 1) {
    const ghost = $("drag-ghost") || Object.assign(document.createElement("div"), { id: "drag-ghost" });
    ghost.className = "drag-ghost";
    ghost.textContent = `${dragUids.size} pages`;
    document.body.appendChild(ghost);
    e.dataTransfer.setDragImage(ghost, 20, 20);
  }
  requestAnimationFrame(() => {
    for (const u of dragUids) cards.get(u)?.classList.add("dragging");
  });
}

function onDragEnd() {
  for (const u of dragUids || []) cards.get(u)?.classList.remove("dragging");
  dragUids = null;
  clearDropMarker();
  $("drag-ghost")?.remove();
}

function dropTargetFromEvent(e) {
  const card = e.target.closest(".card");
  if (card) {
    const r = card.getBoundingClientRect();
    return { el: card, after: e.clientX > r.left + r.width / 2 };
  }
  const last = grid.lastElementChild;
  return last ? { el: last, after: true } : null;
}

grid.addEventListener("dragover", (e) => {
  if (!dragUids) return;
  e.preventDefault();
  e.dataTransfer.dropEffect = "move";
  const t = dropTargetFromEvent(e);
  if (!t) return;
  if (dropMarker && dropMarker.el === t.el && dropMarker.after === t.after) return;
  clearDropMarker();
  t.el.classList.add(t.after ? "drop-after" : "drop-before");
  dropMarker = t;
});

grid.addEventListener("drop", (e) => {
  if (!dragUids) return;
  e.preventDefault();
  const t = dropTargetFromEvent(e);
  const uids = dragUids;
  onDragEnd();
  if (!t) return;
  // Find the first page after the drop point that is not itself being moved.
  let idx = state.pages.findIndex((p) => p.uid === Number(t.el.dataset.uid)) + (t.after ? 1 : 0);
  while (idx < state.pages.length && uids.has(state.pages[idx].uid)) idx++;
  moveTo(uids, idx < state.pages.length ? state.pages[idx].uid : null);
});

// ---- rendering -----------------------------------------------------------

function makeCard(item) {
  const src = state.sources.get(item.src);
  const card = document.createElement("div");
  card.className = "card";
  card.draggable = true;
  card.dataset.uid = item.uid;
  card.style.setProperty("--src-color", src.color);

  const img = document.createElement("img");
  img.loading = "lazy";
  img.decoding = "async";
  img.draggable = false;
  img.alt = `${src.name} page ${item.page + 1}`;
  card.appendChild(img);

  const label = document.createElement("div");
  label.className = "label";
  label.innerHTML = `<span class="num"></span><span class="badge"></span>`;
  label.querySelector(".badge").textContent = `${src.name} · p${item.page + 1}`;
  label.querySelector(".badge").title = src.name;
  card.appendChild(label);

  card.addEventListener("click", (e) => onCardClick(e, item.uid));
  card.addEventListener("dblclick", () => openPreview(item.uid));
  card.addEventListener("dragstart", (e) => onDragStart(e, item.uid));
  card.addEventListener("dragend", onDragEnd);
  return card;
}

function thumbRequestWidth() {
  // Request in coarse steps so the browser cache is reused while resizing.
  const px = state.thumbWidth * (window.devicePixelRatio || 1);
  return Math.ceil(px / 100) * 100;
}

function render() {
  const reqW = thumbRequestWidth();
  grid.style.setProperty("--thumb-w", `${state.thumbWidth}px`);

  const live = new Set();
  state.pages.forEach((item, i) => {
    let card = cards.get(item.uid);
    if (!card) {
      card = makeCard(item);
      cards.set(item.uid, card);
    }
    live.add(item.uid);
    const img = card.firstChild;
    const url = pageUrl(item.src, item.page, reqW);
    if (img.getAttribute("src") !== url) img.src = url;
    card.querySelector(".num").textContent = i + 1;
    card.classList.toggle("selected", state.selected.has(item.uid));
    if (grid.children[i] !== card) grid.insertBefore(card, grid.children[i] || null);
  });
  // Detach cards for deleted pages (kept in `cards` so undo can reuse them).
  for (const el of Array.from(grid.children)) {
    if (!live.has(Number(el.dataset.uid))) el.remove();
  }
  for (const uid of state.selected) if (!live.has(uid)) state.selected.delete(uid);

  renderSources();
  updateControls();
}

function renderSources() {
  const box = $("sources");
  box.replaceChildren();
  const counts = new Map();
  for (const p of state.pages) counts.set(p.src, (counts.get(p.src) || 0) + 1);
  for (const src of state.sources.values()) {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.style.setProperty("--src-color", src.color);
    chip.textContent = `${src.name} (${counts.get(src.id) || 0}/${src.page_count})`;
    chip.title = src.path || src.name;
    box.appendChild(chip);
  }
}

function updateControls() {
  const hasDoc = state.sources.size > 0;
  const n = state.pages.length;
  const s = state.selected.size;
  $("empty").hidden = hasDoc;
  $("btn-append").disabled = !hasDoc;
  $("btn-delete").disabled = !s;
  $("btn-start").disabled = !s;
  $("btn-end").disabled = !s;
  $("btn-undo").disabled = !state.undo.length;
  $("btn-redo").disabled = !state.redo.length;
  $("btn-save").disabled = !n;
  $("status-text").textContent = hasDoc
    ? `${n} page${n === 1 ? "" : "s"}${s ? ` · ${s} selected` : ""}${state.dirty ? " · unsaved changes" : ""}`
    : "No document";
  document.title = hasDoc ? `${state.dirty ? "• " : ""}PDF Editor` : "PDF Editor";
}

// ---- preview -------------------------------------------------------------

let previewIndex = -1;

function openPreview(uid) {
  previewIndex = state.pages.findIndex((p) => p.uid === uid);
  if (previewIndex < 0) return;
  showPreviewPage();
  $("preview").showModal();
}

function showPreviewPage() {
  const item = state.pages[previewIndex];
  const src = state.sources.get(item.src);
  const w = Math.min(2400, Math.ceil((Math.min(window.innerWidth, 1400) * (window.devicePixelRatio || 1)) / 200) * 200);
  $("prev-img").src = pageUrl(item.src, item.page, w);
  $("prev-label").textContent = `Page ${previewIndex + 1} of ${state.pages.length} — ${src.name} p${item.page + 1}`;
  $("prev-back").disabled = previewIndex === 0;
  $("prev-next").disabled = previewIndex === state.pages.length - 1;
}

function stepPreview(delta) {
  const i = previewIndex + delta;
  if (i < 0 || i >= state.pages.length) return;
  previewIndex = i;
  showPreviewPage();
}

$("prev-back").addEventListener("click", () => stepPreview(-1));
$("prev-next").addEventListener("click", () => stepPreview(1));
$("prev-close").addEventListener("click", () => $("preview").close());
$("preview").addEventListener("click", (e) => {
  if (e.target.classList.contains("preview-body")) $("preview").close();
});

// ---- wiring --------------------------------------------------------------

$("btn-open").addEventListener("click", () => guarded(openDocument));
$("btn-open-empty").addEventListener("click", () => guarded(openDocument));
$("btn-append").addEventListener("click", () => guarded(appendDocuments));
$("btn-delete").addEventListener("click", deleteSelected);
$("btn-start").addEventListener("click", () => moveSelected(true));
$("btn-end").addEventListener("click", () => moveSelected(false));
$("btn-undo").addEventListener("click", undo);
$("btn-redo").addEventListener("click", redo);
$("btn-save").addEventListener("click", () => guarded(saveDocument));
$("zoom").addEventListener("input", (e) => {
  state.thumbWidth = Number(e.target.value);
  render();
});

// Clicking empty grid space clears the selection.
grid.addEventListener("click", (e) => {
  if (e.target === grid && state.selected.size) {
    state.selected.clear();
    render();
  }
});

document.addEventListener("keydown", (e) => {
  const ctrl = e.ctrlKey || e.metaKey;
  if ($("preview").open) {
    if (e.key === "ArrowLeft") stepPreview(-1);
    else if (e.key === "ArrowRight") stepPreview(1);
    return;
  }
  if (document.querySelector("dialog[open]")) return;
  const key = e.key.toLowerCase();
  if (ctrl && key === "o") { e.preventDefault(); guarded(openDocument); }
  else if (ctrl && key === "s") { e.preventDefault(); if (state.pages.length) guarded(saveDocument); }
  else if (ctrl && key === "a") { e.preventDefault(); state.pages.forEach((p) => state.selected.add(p.uid)); render(); }
  else if (ctrl && (key === "y" || (key === "z" && e.shiftKey))) { e.preventDefault(); redo(); }
  else if (ctrl && key === "z") { e.preventDefault(); undo(); }
  else if (e.key === "Delete" || e.key === "Backspace") { e.preventDefault(); deleteSelected(); }
  else if (e.key === "Escape") { state.selected.clear(); render(); }
  else if (e.key === "Enter" && state.anchor != null) openPreview(state.anchor);
});

window.addEventListener("beforeunload", (e) => {
  if (state.dirty) {
    e.preventDefault();
    e.returnValue = "";
  }
});

// Drop the token from the address bar so it isn't kept in browser history.
history.replaceState(null, "", "/");
render();
