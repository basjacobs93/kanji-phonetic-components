let searchIndex = [];
let fuse = null;
let phoneticsData = [];
let radicalsData = [];

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

async function init() {
  const [indexResp, phonResp, radResp] = await Promise.all([
    fetch("data/search-index.json"),
    fetch("data/phonetics.json"),
    fetch("data/radicals.json"),
  ]);

  searchIndex = await indexResp.json();
  phoneticsData = await phonResp.json();
  radicalsData = await radResp.json();

  fuse = new Fuse(searchIndex, {
    keys: [
      { name: "c", weight: 3 },
      { name: "m", weight: 2 },
      { name: "on", weight: 1.5 },
      { name: "kun", weight: 1 },
    ],
    threshold: 0.3,
    includeScore: true,
  });

  setupTabs();
  setupSearch();
  setupGrade();
  setupJlpt();
  setupRadicals();
  setupPhonetics();
  setupDetail();

  // Show some initial kanji (most frequent)
  const initial = searchIndex
    .filter((k) => k.f)
    .sort((a, b) => a.f - b.f)
    .slice(0, 100);
  renderGrid(initial, "#results");
}

function setupTabs() {
  $$(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      $$(".tab").forEach((t) => t.classList.remove("active"));
      $$(".panel").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      $(`#panel-${tab.dataset.tab}`).classList.add("active");
      if (tab.dataset.tab === "search") $("#search").focus();
    });
  });
}

function setupSearch() {
  let timeout;
  $("#search").addEventListener("input", (e) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      const query = e.target.value.trim();
      if (!query) {
        const initial = searchIndex
          .filter((k) => k.f)
          .sort((a, b) => a.f - b.f)
          .slice(0, 100);
        renderGrid(initial, "#results");
        return;
      }
      // Direct character match first
      const exact = searchIndex.filter((k) => k.c === query);
      if (exact.length > 0) {
        renderGrid(exact, "#results");
        return;
      }
      const results = fuse.search(query, { limit: 100 }).map((r) => r.item);
      renderGrid(results, "#results");
    }, 150);
  });
}

function setupGrade() {
  const grades = [
    { value: 1, label: "Grade 1" },
    { value: 2, label: "Grade 2" },
    { value: 3, label: "Grade 3" },
    { value: 4, label: "Grade 4" },
    { value: 5, label: "Grade 5" },
    { value: 6, label: "Grade 6" },
    { value: 8, label: "Secondary" },
    { value: 9, label: "Jinmeiyou" },
  ];
  const container = $("#grade-buttons");
  grades.forEach((g) => {
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.textContent = g.label;
    btn.addEventListener("click", () => {
      container.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const results = searchIndex
        .filter((k) => k.g === g.value)
        .sort((a, b) => (a.f || 9999) - (b.f || 9999));
      renderGrid(results, "#grade-results");
    });
    container.appendChild(btn);
  });
}

function setupJlpt() {
  const levels = [
    { value: 4, label: "N5 (easiest)" },
    { value: 3, label: "N4" },
    { value: 2, label: "N3" },
    { value: 1, label: "N2" },
  ];
  const container = $("#jlpt-buttons");
  levels.forEach((l) => {
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.textContent = l.label;
    btn.addEventListener("click", () => {
      container.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const results = searchIndex
        .filter((k) => k.j === l.value)
        .sort((a, b) => (a.f || 9999) - (b.f || 9999));
      renderGrid(results, "#jlpt-results");
    });
    container.appendChild(btn);
  });
}

function setupRadicals() {
  const container = $("#radical-list");
  radicalsData.forEach((r) => {
    const btn = document.createElement("button");
    btn.className = "radical-btn";
    btn.innerHTML = `<span class="char">${r.c}</span><span class="count">${r.count}</span>`;
    btn.addEventListener("click", () => {
      container.querySelectorAll(".radical-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const results = searchIndex
        .filter((k) => k.r === r.n)
        .sort((a, b) => (a.f || 9999) - (b.f || 9999));
      renderGrid(results, "#radical-results");
    });
    container.appendChild(btn);
  });
}

function setupPhonetics() {
  const container = $("#phonetic-list");
  phoneticsData.forEach((p) => {
    const btn = document.createElement("button");
    btn.className = "phonetic-btn";
    btn.innerHTML = `<span class="char">${p.char}</span><span class="count">${p.reading}</span>`;
    btn.addEventListener("click", () => {
      container.querySelectorAll(".phonetic-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const results = searchIndex
        .filter((k) => k.p === p.char)
        .sort((a, b) => (a.f || 9999) - (b.f || 9999));
      renderGrid(results, "#phonetic-results");
    });
    container.appendChild(btn);
  });
}

function renderGrid(items, selector) {
  const grid = $(selector);
  if (items.length === 0) {
    grid.innerHTML = '<div class="empty-state">No kanji found.</div>';
    return;
  }
  grid.innerHTML = items
    .map(
      (k) =>
        `<div class="kanji-card" data-cp="${k.cp}" data-char="${k.c}">
          <span class="char">${k.c}</span>
          <span class="meaning">${k.m || ""}</span>
        </div>`
    )
    .join("");
}

function setupDetail() {
  const overlay = $("#detail-overlay");
  const content = $("#detail-content");

  // Close
  $("#close-detail").addEventListener("click", () => overlay.classList.add("hidden"));
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.classList.add("hidden");
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") overlay.classList.add("hidden");
  });

  // Open on card click (delegated)
  document.addEventListener("click", async (e) => {
    const card = e.target.closest(".kanji-card");
    if (!card) return;
    const cp = card.dataset.cp;
    if (!cp) return;
    await showDetail(cp);
  });

  // Related kanji click
  content.addEventListener("click", async (e) => {
    const btn = e.target.closest(".related-btn");
    if (!btn) return;
    const char = btn.dataset.char;
    const cp = char.codePointAt(0).toString(16).padStart(5, "0");
    await showDetail(cp);
  });
}

async function showDetail(codepoint) {
  const overlay = $("#detail-overlay");
  const content = $("#detail-content");
  content.innerHTML = '<div class="loading">Loading...</div>';
  overlay.classList.remove("hidden");

  const resp = await fetch(`data/kanji/${codepoint}.json`);
  if (!resp.ok) {
    content.innerHTML = '<div class="empty-state">Kanji data not found.</div>';
    return;
  }
  const k = await resp.json();

  let legendHtml = '<div class="component-legend">';
  if (k.radical) {
    legendHtml += `
      <div class="legend-item">
        <span class="legend-swatch" style="background:var(--radical)"></span>
        <span class="legend-char">${k.radical.char}</span>
        <span class="legend-label">${k.radical.name} (radical)</span>
      </div>`;
  }
  if (k.phonetic) {
    legendHtml += `
      <div class="legend-item">
        <span class="legend-swatch" style="background:var(--phonetic)"></span>
        <span class="legend-char">${k.phonetic.char}</span>
        <span class="legend-label">${k.phonetic.reading} "${k.phonetic.name}" (phonetic)</span>
      </div>`;
  }
  if (!k.radical && !k.phonetic) {
    legendHtml += '<div class="legend-item"><span class="legend-label">No component data available</span></div>';
  }
  legendHtml += "</div>";

  let metaHtml = '<div class="detail-meta">';
  if (k.strokes) metaHtml += `<span class="meta-tag">${k.strokes} strokes</span>`;
  if (k.grade) metaHtml += `<span class="meta-tag">Grade ${k.grade === 8 ? "Secondary" : k.grade === 9 ? "Jinmeiyou" : k.grade}</span>`;
  if (k.jlpt) metaHtml += `<span class="meta-tag">JLPT N${5 - k.jlpt}</span>`;
  if (k.freq) metaHtml += `<span class="meta-tag">Freq #${k.freq}</span>`;
  metaHtml += "</div>";

  let relatedHtml = "";
  if (k.related_phonetic && k.related_phonetic.length > 0) {
    relatedHtml += `
      <div class="related-section">
        <h3>Same phonetic component (${k.phonetic.char} ${k.phonetic.reading})</h3>
        <div class="related-kanji">
          ${k.related_phonetic.map((c) => `<button class="related-btn" data-char="${c}">${c}</button>`).join("")}
        </div>
      </div>`;
  }

  content.innerHTML = `
    <div class="detail-header">
      <div class="detail-svg">${k.svg}</div>
      <div class="detail-info">
        <h2>${k.character}</h2>
        <div class="detail-meanings">${k.meanings.join(", ")}</div>
        <div class="detail-readings">
          ${k.on.length ? `<span><strong>ON:</strong> ${k.on.join(", ")}</span>` : ""}
          ${k.kun.length ? `<span><strong>KUN:</strong> ${k.kun.join(", ")}</span>` : ""}
        </div>
      </div>
    </div>
    ${legendHtml}
    ${metaHtml}
    ${relatedHtml}
  `;
}

init();
