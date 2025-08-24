// ===== Utilities =====
const AQI_THEME = [
  { max: 50, cls: "good",          label: "Good",             hero: "clear & fresh",      sub: "breathe easy" },
  { max: 100, cls: "moderate",      label: "Moderate",         hero: "fair air",           sub: "generally acceptable" },
  { max: 150, cls: "usg",           label: "Unhealthy (SG)",   hero: "sensitive groups",   sub: "limit prolonged exertion" },
  { max: 200, cls: "unhealthy",     label: "Unhealthy",        hero: "mask up outdoors",   sub: "reduce outdoor time" },
  { max: 300, cls: "veryunhealthy", label: "Very Unhealthy",   hero: "avoid outdoor activity", sub: "stay indoors when possible" },
  { max: 999, cls: "hazardous",     label: "Hazardous",        hero: "health alert",       sub: "remain indoors" },
];

function classifyAQI(aqi){
  return AQI_THEME.find(t => aqi <= t.max) || AQI_THEME[AQI_THEME.length - 1];
}

function badgeStyle(hex){ return `background:${hex}22;border:1px solid ${hex}55;color:${hex}`; }

function timeoutFetch(resource, options = {}) {
  const { timeout = 12000, ...rest } = options;
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  return fetch(resource, { ...rest, signal: controller.signal }).finally(() => clearTimeout(id));
}

async function fetchJSON(url){
  const res = await timeoutFetch(url, { headers: { "accept": "application/json" }});
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function setBodyTheme(aqi){
  const theme = classifyAQI(Number(aqi) || 0).cls;
  document.body.className = theme;
}

function setHero(aqi, city, label){
  const t = classifyAQI(Number(aqi) || 0);
  document.getElementById("heroTitle").textContent = t.hero;
  const c = city || "—";
  document.getElementById("heroSub").textContent = `${c} • AQI ${aqi} (${label || t.label})`;
}

// ===== Renderers =====
function renderSnapshot(el, data){
  const theme = classifyAQI(data.aqi);
  setBodyTheme(data.aqi);
  setHero(data.aqi, data.city, data.category?.label);

  const w = data.weather || {};
  const p = data.pollutants || {};

  el.innerHTML = `
    <h3>${data.city}
      <span class="badge" style="${badgeStyle(data.category?.color || "#9fb0d9")}">
        ${data.category?.label || theme.label} · AQI ${data.aqi}
      </span>
    </h3>
    <small>Updated: ${data.updated_at} · Source: ${data.source}</small>
    <div class="meta-grid" style="margin-top:10px;">
      <div class="kv"><b>Coordinates</b> <span>${data.coordinates.lat.toFixed(2)}, ${data.coordinates.lon.toFixed(2)}</span></div>
      <div class="kv"><b>Weather</b> <span>${w?.temp_c ?? "—"}°C · ${w?.humidity_pct ?? "—"}% RH</span></div>
      <div class="kv"><b>PM2.5</b> <span class="pill">${p.pm25 ?? "—"}</span></div>
      <div class="kv"><b>PM10</b>  <span class="pill">${p.pm10 ?? "—"}</span></div>
      <div class="kv"><b>NO₂</b>   <span class="pill">${p.no2 ?? "—"}</span></div>
      <div class="kv"><b>O₃</b>    <span class="pill">${p.o3 ?? "—"}</span></div>
    </div>
  `;
  el.classList.remove("skeleton"); el.setAttribute("aria-busy","false");
}

function renderInsights(el, data){
  const lines = [data.recommendation].filter(Boolean);
  if (data.anomaly) lines.push(`⚠ ${data.anomaly}`);
  el.innerHTML = `<h3>Health & Activity</h3><p>${lines.join("<br/>")}</p>`;
  el.classList.remove("skeleton"); el.setAttribute("aria-busy","false");
}

function renderForecast(el, data){
  const points = (data?.points || []).slice(0, 24);
  const list = points.map(p => {
    const t = p.ts.includes("T") ? p.ts.split("T")[1].slice(0,5) : p.ts;
    return `${t} · AQI ${Math.round(p.aqi)}`;
  }).join("\n");

  const min = points.reduce((m,p)=>Math.min(m,p.aqi), Number.POSITIVE_INFINITY);
  const max = points.reduce((m,p)=>Math.max(m,p.aqi), 0);
  const avg = points.reduce((s,p)=>s+p.aqi,0) / (points.length || 1);

  el.innerHTML = `
    <h3>Next ${data.horizon}h Forecast</h3>
    <div class="row" style="margin:8px 0 10px;">
      <span class="pill">min ${isFinite(min)?min.toFixed(0):"—"}</span>
      <span class="pill">max ${max?max.toFixed(0):"—"}</span>
      <span class="pill">avg ${avg?avg.toFixed(0):"—"}</span>
    </div>
    <div class="code" aria-label="forecast timeline">${list || "—"}</div>
  `;
  el.classList.remove("skeleton"); el.setAttribute("aria-busy","false");
}

// ===== Map Renderer =====
let map = null;
let markerLayer = null;
let heatLayer = null;

function renderMap(coords, aqi, category) {
  const mapDiv = document.getElementById("map");
  const mapCard = mapDiv.parentElement;
  mapCard.classList.remove("skeleton");
  mapCard.setAttribute("aria-busy", "false");

  // Reset previous map if exists
  if (map) {
    map.remove();
    map = null;
    markerLayer = null;
    heatLayer = null;
    mapDiv.innerHTML = "";
  }

  mapDiv.style.height = "270px";
  mapDiv.style.width = "100%";

  map = L.map("map").setView([coords.lat, coords.lon], 11);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  markerLayer = L.layerGroup().addTo(map);

  function normalizeAQI(aqi) {
    if (aqi <= 50) return 0.2;
    if (aqi <= 100) return 0.4;
    if (aqi <= 200) return 0.7;
    if (aqi <= 300) return 0.85;
    return 1.0;
  }
  const intensity = normalizeAQI(aqi);

  heatLayer = L.heatLayer([[coords.lat, coords.lon, intensity]], {
    radius: 35,
    blur: 20,
    maxZoom: 12,
    gradient: {
      0.2: "green",
      0.4: "yellow",
      0.7: "orange",
      0.85: "purple",
      1.0: "red"
    }
  }).addTo(map);

  L.marker([coords.lat, coords.lon])
    .addTo(markerLayer)
    .bindPopup(`<b>${category?.label || "AQI"}</b><br>AQI: ${aqi}`)
    .openPopup();

  map.setView([coords.lat, coords.lon], 11);
}

// ===== Orchestration =====
async function onSearch(){
  const btn = document.getElementById("btnSearch");
  const city = (document.getElementById("city").value || "").trim() || "Delhi";

  const snapEl = document.getElementById("snapshot");
  const insEl = document.getElementById("insights");
  const fEl = document.getElementById("forecast");

  [snapEl, insEl, fEl].forEach(el => { 
    el.classList.add("skeleton"); 
    el.setAttribute("aria-busy","true"); 
    el.innerHTML = ""; 
  });

  btn.disabled = true;
  try{
    const snap = await fetchJSON(`/api/v1/search?city=${encodeURIComponent(city)}`);
    renderSnapshot(snapEl, snap);

    const [ins, fc] = await Promise.all([
      fetchJSON(`/api/v1/insights/current?city=${encodeURIComponent(city)}`),
      fetchJSON(`/api/v1/insights/forecast?city=${encodeURIComponent(city)}&horizon=24`)
    ]);
    renderInsights(insEl, ins);
    renderForecast(fEl, fc);

    // Map rendering
    renderMap(snap.coordinates, snap.aqi, snap.category);

    // AQI badge in map card (optional UI element)
    const mapAqiBadge = document.getElementById("mapAqiBadge");
    if (mapAqiBadge) {
      const theme = classifyAQI(snap.aqi);
      mapAqiBadge.textContent = `${snap.category?.label || theme.label} · AQI ${snap.aqi}`;
      mapAqiBadge.style = badgeStyle(snap.category?.color || "#9fb0d9");
    }

    localStorage.setItem("airsight:lastCity", city);
  } catch(err){
    const msg = (err && err.message) ? err.message : "Something went wrong";
    snapEl.innerHTML = `<h3>Oops</h3><p>${msg}</p>`;
    [insEl, fEl].forEach(el => el.innerHTML = "");
    setHero("--", city, "");
  } finally {
    btn.disabled = false;
  }
}

// ===== UX niceties =====
document.getElementById("btnSearch").addEventListener("click", onSearch);
document.getElementById("city").addEventListener("keydown", (e) => {
  if (e.key === "Enter") onSearch();
});

window.addEventListener("DOMContentLoaded", () => {
  const last = localStorage.getItem("airsight:lastCity");
  if (last) document.getElementById("city").value = last;
  onSearch();
});
