const byId = (id) => document.getElementById(id);
const $ = (sel, root = document) => root.querySelector(sel);

let DATA = null;
let SOURCE_MAP = new Map();
let ACTIVE_COMPETITOR = "all";

const safe = (v, fallback = "Chưa có dữ liệu") =>
  v === null || v === undefined || v === "" ? fallback : String(v);

const isPlaceholder = (data) => data?.edition?.status === "placeholder";

function formatNumber(v) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return "Chưa có dữ liệu";
  return new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(Number(v));
}

function formatDateTime(iso) {
  if (!iso) return "Chưa có thời gian cập nhật";
  try {
    return new Intl.DateTimeFormat("vi-VN", {
      timeZone: "Asia/Ho_Chi_Minh",
      day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit"
    }).format(new Date(iso));
  } catch { return iso; }
}

function freshness(iso) {
  if (!iso) return "Chưa xác định độ mới";
  const diff = Date.now() - new Date(iso).getTime();
  const h = Math.max(0, diff / 3600000);
  if (h < 1) return "Cập nhật trong vòng 1 giờ";
  if (h < 24) return `Cập nhật khoảng ${Math.round(h)} giờ trước`;
  return `Cập nhật khoảng ${Math.round(h / 24)} ngày trước`;
}

function humanSession(s) {
  if (s === "morning") return "Bản sáng";
  if (s === "afternoon") return "Bản chiều";
  if (s === "evening") return "Bản tối";
  if (s === "adhoc") return "Bản cập nhật";
  return "Bản tin";
}

function sentimentLabel(s) {
  const map = {
    positive: ["Tích cực", "#20a66a", "#eaf8f1"],
    neutral: ["Trung tính", "#63758a", "#eef2f7"],
    negative: ["Tiêu cực", "#e14d4d", "#fff0f0"],
    mixed: ["Trái chiều", "#d58a00", "#fff7da"]
  };
  return map[s] || ["Chưa phân loại", "#63758a", "#eef2f7"];
}

function metricIcon(category) {
  const map = {
    fx: "FX", gold: "Au", equity: "VN", rates: "%", commodity: "Oil",
    crypto: "₿", macro: "M", retail: "R", ecommerce: "EC",
    consumer: "C", camera: "CAM", other: "•"
  };
  return map[category] || "•";
}

function metricChange(m) {
  if (m?.change === null || m?.change === undefined) return ["—", "change-na"];
  const n = Number(m.change);
  const symbol = n > 0 ? "↑" : n < 0 ? "↓" : "→";
  const cls = n > 0 ? "change-up" : n < 0 ? "change-down" : "change-flat";
  return [`${symbol} ${formatNumber(Math.abs(n))}${m.change_unit ? ` ${m.change_unit}` : ""}`, cls];
}

function metricValue(m) {
  if (m?.value === null || m?.value === undefined) return "Chưa có dữ liệu";
  return `${formatNumber(m.value)}${m.unit ? ` ${m.unit}` : ""}`;
}

function sourceLinks(ids = []) {
  const wrap = document.createElement("div");
  wrap.className = "source-chips";
  ids.forEach(id => {
    const s = SOURCE_MAP.get(id);
    if (!s) return;
    const a = document.createElement("a");
    a.className = "source-chip";
    a.href = s.url || "#";
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = s.publisher || s.title || id;
    a.title = s.title || id;
    wrap.appendChild(a);
  });
  return wrap;
}

function placeholder(el, text = "Chưa có mục nào trong bản tin hiện tại.") {
  if (!el) return;
  el.innerHTML = `<div class="placeholder-box">${text}</div>`;
}

function renderKeyPoints(points = []) {
  const el = byId("key-points");
  el.innerHTML = "";
  if (!points.length) return placeholder(el, "Bản tin hiện tại chưa có key points.");
  points.forEach(p => {
    const div = document.createElement("div");
    div.className = "key-point";
    div.textContent = safe(p);
    el.appendChild(div);
  });
}

function renderDataGaps(gaps = []) {
  const el = byId("data-gaps");
  el.innerHTML = "";
  if (!gaps.length) {
    el.innerHTML = `<div class="empty-note">Không ghi nhận khoảng trống dữ liệu đáng kể.</div>`;
    return;
  }
  gaps.forEach(g => {
    const div = document.createElement("div");
    div.className = "data-gap-item";
    div.textContent = safe(g);
    el.appendChild(div);
  });
}

function renderMetrics(containerId, metrics = []) {
  const el = byId(containerId);
  if (!el) return;
  el.innerHTML = "";
  if (!metrics.length) return placeholder(el);
  metrics.forEach(m => {
    const node = byId("metric-template").content.cloneNode(true);
    node.querySelector(".metric-icon").textContent = metricIcon(m.category);
    node.querySelector(".metric-label").textContent = safe(m.label);
    node.querySelector(".metric-value").textContent = metricValue(m);
    const [change, cls] = metricChange(m);
    const changeEl = node.querySelector(".metric-change");
    changeEl.textContent = change;
    changeEl.classList.add(cls);
    node.querySelector(".metric-period").textContent = safe(m.period, "");
    const note = node.querySelector(".metric-note");
    note.textContent = safe(m.note, "");
    if (!m.note) note.style.display = "none";
    el.appendChild(node);
  });
}

function renderMiniMetrics(containerId, metrics = []) {
  const el = byId(containerId);
  if (!el) return;
  el.innerHTML = "";
  if (!metrics.length) return;
  metrics.slice(0, 4).forEach(m => {
    const d = document.createElement("div");
    d.className = "mini-metric";
    d.innerHTML = `<span>${safe(m.label)}</span><strong>${metricValue(m)}</strong>`;
    el.appendChild(d);
  });
}

function levelClass(v) {
  return v === "high" ? "level-high" : v === "medium" ? "level-medium" : v === "low" ? "level-low" : "level-na";
}

function levelText(v) {
  return v === "high" ? "Cao" : v === "medium" ? "Trung bình" : v === "low" ? "Thấp" : "—";
}

function renderStack(containerId, items = [], config = {}) {
  const el = byId(containerId);
  if (!el) return;
  el.innerHTML = "";
  if (!items.length) return placeholder(el);
  items.forEach(item => {
    const node = byId("stack-template").content.cloneNode(true);
    const badge = node.querySelector(".stack-badge");
    badge.textContent = safe(item[config.badge] ?? item.category ?? item.theme ?? item.signal_type ?? item.channel_type, "Insight");

    const level = node.querySelector(".stack-level");
    const levelVal = item[config.level] ?? item.impact ?? item.strength;
    if (["high","medium","low"].includes(levelVal)) {
      level.textContent = levelText(levelVal);
      level.classList.add(levelClass(levelVal));
    } else if (levelVal) {
      level.textContent = safe(levelVal);
      level.classList.add("level-na");
    } else {
      level.style.display = "none";
    }

    node.querySelector(".stack-title").textContent = safe(item[config.title] ?? item.title ?? item.theme ?? item.trend ?? item.signal ?? item.indicator ?? item.development);
    node.querySelector(".stack-detail").textContent = safe(item[config.detail] ?? item.detail ?? item.description ?? item.implication_for_fpt_camera ?? "");
    const chips = node.querySelector(".source-chips");
    chips.replaceWith(sourceLinks(item.source_ids || []));
    el.appendChild(node);
  });
}

function renderTraffic(items = []) {
  const el = byId("traffic-lights");
  el.innerHTML = "";
  if (!items.length) return placeholder(el);
  items.forEach(item => {
    const node = byId("traffic-template").content.cloneNode(true);
    const card = node.querySelector(".traffic-card");
    card.classList.add(`status-${item.status || "none"}`);
    node.querySelector(".traffic-name").textContent = safe(item.name);
    node.querySelector(".traffic-trend").textContent =
      item.trend === "improving" ? "Đang cải thiện" :
      item.trend === "worsening" ? "Đang xấu đi" :
      item.trend === "stable" ? "Ổn định" : "—";
    node.querySelector(".traffic-explanation").textContent = safe(item.explanation);
    node.querySelector(".traffic-action").textContent = safe(item.action);
    const chips = node.querySelector(".source-chips");
    chips.replaceWith(sourceLinks(item.source_ids || []));
    el.appendChild(node);
  });
}

function priorityClass(v) {
  return v === "high" ? "priority-high" : v === "medium" ? "priority-medium" : "priority-low";
}

function renderRecommendations(items = []) {
  const el = byId("recommendations");
  el.innerHTML = "";
  if (!items.length) return placeholder(el);
  items.forEach(item => {
    const node = byId("recommendation-template").content.cloneNode(true);
    const p = node.querySelector(".priority-pill");
    p.textContent = `Ưu tiên ${levelText(item.priority)}`;
    p.classList.add(priorityClass(item.priority));
    node.querySelector(".owner-pill").textContent = safe(item.owner, "Owner chưa rõ");
    node.querySelector(".recommendation-issue").textContent = safe(item.issue);
    node.querySelector(".recommendation-evidence").textContent = safe(item.evidence);
    node.querySelector(".recommendation-action").textContent = safe(item.action);
    node.querySelector(".deadline").textContent = `Hạn: ${safe(item.deadline, "—")}`;
    node.querySelector(".kpi").textContent = `KPI: ${safe(item.kpi, "—")}`;
    const chips = node.querySelector(".source-chips");
    chips.replaceWith(sourceLinks(item.source_ids || []));
    el.appendChild(node);
  });
}

function renderDecisions(items = []) {
  const el = byId("decisions");
  el.innerHTML = "";
  if (!items.length) return placeholder(el);
  items.forEach(item => {
    const card = document.createElement("article");
    card.className = "decision-card";
    const options = (item.options || []).map(o => {
      const cls = o === item.recommended_option ? "option-item recommended" : "option-item";
      return `<div class="${cls}">${safe(o)}</div>`;
    }).join("");
    card.innerHTML = `
      <div class="decision-top">
        <span class="priority-pill ${priorityClass(item.urgency)}">${levelText(item.urgency)}</span>
        <span class="owner-pill">${safe(item.owner)}</span>
      </div>
      <h4>${safe(item.decision)}</h4>
      <p>${safe(item.context)}</p>
      <div class="options-list">${options}</div>
      <div class="recommendation-meta">
        <span>Hạn: ${safe(item.deadline)}</span>
      </div>
    `;
    card.appendChild(sourceLinks(item.source_ids || []));
    el.appendChild(card);
  });
}

function renderScenarios(items = []) {
  const el = byId("scenarios");
  el.innerHTML = "";
  if (!items.length) return placeholder(el);
  const order = { base:0, upside:1, downside:2 };
  [...items].sort((a,b)=>(order[a.type]??9)-(order[b.type]??9)).forEach(item => {
    const node = byId("scenario-template").content.cloneNode(true);
    const card = node.querySelector(".scenario-card");
    card.classList.add(`type-${item.type || "base"}`);
    node.querySelector(".scenario-type").textContent =
      item.type === "base" ? "Cơ sở" : item.type === "upside" ? "Tích cực" : item.type === "downside" ? "Tiêu cực" : safe(item.type);
    node.querySelector(".scenario-likelihood").textContent = item.likelihood ? `Khả năng: ${levelText(item.likelihood)}` : "";
    node.querySelector(".scenario-title").textContent = safe(item.scenario);
    node.querySelector(".scenario-conditions").textContent = safe(item.conditions);
    node.querySelector(".scenario-consumer").textContent = safe(item.consumer_impact);
    node.querySelector(".scenario-b2c").textContent = safe(item.b2c_impact);
    node.querySelector(".scenario-camera").textContent = safe(item.fpt_camera_impact);
    node.querySelector(".scenario-action").textContent = `Hành động: ${safe(item.action)}`;
    const chips = node.querySelector(".source-chips");
    chips.replaceWith(sourceLinks(item.source_ids || []));
    el.appendChild(node);
  });
}

function renderEvents(items = []) {
  renderStack("events", items, { title:"event", detail:"why_it_matters", badge:"category", level:"importance" });
}

function renderMustRead(items = []) {
  const el = byId("must-read");
  el.innerHTML = "";
  if (!items.length) return placeholder(el);
  items.forEach(item => {
    const a = document.createElement("a");
    a.className = "must-read-card";
    a.href = item.url || "#";
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.innerHTML = `
      <div class="publisher">${safe(item.publisher)}</div>
      <h4>${safe(item.title)}</h4>
      <p>${safe(item.summary)}</p>
      <div class="why">${safe(item.why_read)}</div>
    `;
    el.appendChild(a);
  });
}

function statusText(v) {
  return v === "expanding" ? "Đang mở rộng" :
         v === "stable" ? "Ổn định" :
         v === "contracting" ? "Thu hẹp" :
         v === "mixed" ? "Trái chiều" : "Chưa xác định";
}

function renderBullets(id, items = []) {
  const el = byId(id);
  el.innerHTML = "";
  if (!items.length) return placeholder(el, "Chưa có mục nào.");
  items.forEach(x => {
    const d = document.createElement("div");
    d.className = "bullet-item";
    d.textContent = safe(x);
    el.appendChild(d);
  });
}

function renderPricing(items = []) {
  const tbody = byId("pricing-watch");
  tbody.innerHTML = "";
  if (!items.length) {
    tbody.innerHTML = `<tr><td colspan="6">Chưa có dữ liệu giá / khuyến mãi.</td></tr>`;
    return;
  }
  items.forEach(item => {
    const tr = document.createElement("tr");
    const price = item.price === null || item.price === undefined ? "—" :
      `${formatNumber(item.price)} ${item.currency || "VND"}`;
    const change = item.change_pct === null || item.change_pct === undefined ? "—" : `${formatNumber(item.change_pct)}%`;
    tr.innerHTML = `
      <td><strong>${safe(item.brand)}</strong></td>
      <td>${safe(item.product)}</td>
      <td>${safe(item.channel, "—")}</td>
      <td>${price}</td>
      <td>${change}</td>
      <td>${safe(item.promo, "—")}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderChannelWatch(items = []) {
  renderStack("channel-watch", items, { title:"channel", detail:"development", badge:"channel_type", level:"direction" });
}

function renderCompetitorFilters(items = []) {
  const el = byId("competitor-filters");
  el.innerHTML = "";
  const brands = [...new Set(items.map(x => x.competitor).filter(Boolean))];
  const all = ["all", ...brands];
  all.forEach(b => {
    const btn = document.createElement("button");
    btn.className = `filter-btn ${ACTIVE_COMPETITOR === b ? "active" : ""}`;
    btn.textContent = b === "all" ? "Tất cả" : b;
    btn.addEventListener("click", () => {
      ACTIVE_COMPETITOR = b;
      renderCompetitorFilters(items);
      renderCompetitors(items);
    });
    el.appendChild(btn);
  });
}

function threatClass(v) {
  return v === "high" ? "threat-high" : v === "medium" ? "threat-medium" : "threat-low";
}

function renderCompetitors(items = []) {
  const el = byId("competitor-watch");
  el.innerHTML = "";
  const filtered = ACTIVE_COMPETITOR === "all" ? items : items.filter(x => x.competitor === ACTIVE_COMPETITOR);
  if (!filtered.length) return placeholder(el, "Chưa có diễn biến đối thủ đáng chú ý.");
  filtered.forEach(item => {
    const node = byId("competitor-template").content.cloneNode(true);
    node.querySelector(".competitor-name").textContent = safe(item.competitor);
    node.querySelector(".development-type").textContent = safe(item.development_type, "other").replaceAll("_"," ");
    const threat = node.querySelector(".threat-pill");
    threat.textContent = `Threat: ${levelText(item.threat_level)}`;
    threat.classList.add(threatClass(item.threat_level));
    node.querySelector(".competitor-development").textContent = safe(item.development);
    node.querySelector(".competitor-channel").textContent = safe(item.channel, "—");
    node.querySelector(".competitor-promo").textContent = safe(item.pricing_or_promo, "—");
    node.querySelector(".competitor-impact").textContent = safe(item.implication_for_fpt_camera);
    const response = node.querySelector(".competitor-response");
    response.textContent = safe(item.suggested_response, "Chưa có phản ứng đề xuất.");
    const chips = node.querySelector(".source-chips");
    chips.replaceWith(sourceLinks(item.source_ids || []));
    el.appendChild(node);
  });
}

function renderSources(items = []) {
  const el = byId("source-list");
  el.innerHTML = "";
  if (!items.length) return placeholder(el, "Chưa có nguồn vì đây có thể là placeholder.");
  items.forEach(s => {
    const a = document.createElement("a");
    a.className = "source-row";
    a.href = s.url || "#";
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.innerHTML = `
      <div class="source-publisher">${safe(s.publisher, "Nguồn")}</div>
      <div class="source-title">${safe(s.title)}</div>
      <div class="source-date">Đăng: ${safe(s.published_at, "—")} · Truy cập: ${safe(s.accessed_at, "—")}</div>
    `;
    el.appendChild(a);
  });
  byId("toggle-sources").style.display = items.length > 9 ? "inline-flex" : "none";
}

function render(data) {
  DATA = data;
  SOURCE_MAP = new Map((data.sources || []).map(s => [s.id, s]));

  byId("edition-title").textContent = safe(data.edition?.title, "B2C Market Intelligence");
  byId("edition-session").textContent = humanSession(data.edition?.session);
  byId("updated-at").textContent = formatDateTime(data.updated_at);
  byId("edition-badge").textContent = `${humanSession(data.edition?.session)} · #${safe(data.edition?.number, "—")}`;
  byId("headline").textContent = safe(data.executive_summary?.headline);
  byId("summary").textContent = safe(data.executive_summary?.summary);
  byId("source-count").textContent = `${(data.sources || []).length} nguồn`;
  byId("freshness").textContent = freshness(data.updated_at);

  const [sentimentText, sentimentColor, sentimentBg] = sentimentLabel(data.executive_summary?.overall_sentiment);
  const sent = byId("overall-sentiment");
  sent.textContent = sentimentText;
  sent.style.color = sentimentColor;
  sent.style.background = sentimentBg;

  renderKeyPoints(data.executive_summary?.key_points || []);
  renderDataGaps(data.executive_summary?.data_gaps || []);

  renderMetrics("market-dashboard", data.market_dashboard || []);

  byId("weekly-summary").textContent = safe(data.weekly_macro_watch?.summary);
  renderStack("weekly-themes", data.weekly_macro_watch?.themes || [], { title:"theme", detail:"detail", badge:"direction", level:"impact" });
  byId("weekly-outlook").textContent = data.weekly_macro_watch?.outlook ? `Outlook · ${data.weekly_macro_watch.outlook}` : "Chưa có outlook.";
  byId("weekly-outlook").style.display = data.weekly_macro_watch?.outlook ? "block" : "none";

  byId("macro24-summary").textContent = safe(data.macro_24h?.summary);
  renderStack("macro24-items", data.macro_24h?.items || [], { title:"title", detail:"detail", badge:"category", level:"impact" });

  byId("financial-summary").textContent = safe(data.financial_markets?.summary);
  renderMiniMetrics("financial-metrics", data.financial_markets?.metrics || []);
  renderStack("financial-highlights", data.financial_markets?.highlights || [], { title:"title", detail:"detail", level:"impact" });

  byId("retail-summary").textContent = safe(data.retail_consumer?.summary);
  renderMiniMetrics("retail-metrics", data.retail_consumer?.metrics || []);
  renderStack("retail-trends", data.retail_consumer?.trends || [], { title:"trend", detail:"detail", badge:"direction", level:"strength" });

  renderTraffic(data.b2c_traffic_lights || []);
  renderRecommendations(data.recommendations || []);
  renderDecisions(data.decisions_today || []);
  renderScenarios(data.scenarios_7d || []);
  renderEvents(data.events_next_24h || []);
  renderMustRead(data.must_read || []);

  const cam = data.camera_market_watch || {};
  byId("camera-summary").textContent = safe(cam.summary);
  byId("camera-status").textContent = statusText(cam.market_status);
  renderMetrics("camera-key-metrics", cam.key_metrics || []);
  byId("camera-impact-state").textContent = sentimentLabel(cam.fpt_camera_impact?.overall)[0];
  byId("camera-impact-summary").textContent = safe(cam.fpt_camera_impact?.summary);
  renderBullets("camera-opportunities", cam.fpt_camera_impact?.opportunities || []);
  renderBullets("camera-risks", cam.fpt_camera_impact?.risks || []);
  renderStack("camera-signals", cam.signals || [], { title:"signal", detail:"detail", badge:"theme", level:"strength" });
  renderStack("camera-demand", cam.demand_watch || [], { title:"indicator", detail:"detail", badge:"segment", level:"strength" });
  renderPricing(cam.pricing_watch || []);
  renderChannelWatch(cam.channel_watch || []);

  renderCompetitorFilters(data.competitor_watch || []);
  renderCompetitors(data.competitor_watch || []);
  renderSources(data.sources || []);

  byId("schema-label").textContent = `Schema ${safe(data.schema_version, "—")}`;

  if (isPlaceholder(data)) {
    document.body.classList.add("is-placeholder");
  } else {
    document.body.classList.remove("is-placeholder");
  }

  document.title = `${safe(data.edition?.title, "B2C Market Intelligence")} | FPT Camera`;
}

function loadData() {
  return fetch(`./data/latest.json?ts=${Date.now()}`, { cache: "no-store" })
    .then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then(render)
    .catch(err => {
      console.error(err);
      byId("edition-title").textContent = "Không tải được dữ liệu";
      byId("headline").textContent = "Dashboard chưa đọc được data/latest.json";
      byId("summary").textContent = "Kiểm tra file data/latest.json đã tồn tại trên cùng repository và GitHub Pages đang publish đúng branch.";
      placeholder(byId("market-dashboard"), `Lỗi tải dữ liệu: ${String(err.message || err)}`);
    });
}

document.querySelectorAll(".nav-pill").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-pill").forEach(x => x.classList.remove("active"));
    btn.classList.add("active");
    const target = document.getElementById(btn.dataset.target);
    if (target) target.scrollIntoView({ behavior:"smooth", block:"start" });
  });
});

byId("toggle-sources").addEventListener("click", () => {
  const list = byId("source-list");
  const collapsed = list.classList.toggle("collapsed");
  byId("toggle-sources").textContent = collapsed ? "Hiện tất cả nguồn" : "Thu gọn nguồn";
});

loadData();
setInterval(loadData, 5 * 60 * 1000);
