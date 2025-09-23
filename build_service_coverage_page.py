#!/usr/bin/env python3
# Writes a complete web app (service_areas.html) for planning technician ZIP coverage.
from pathlib import Path
import json

OUT = Path("service_areas.html")
DEFAULT_TECHS = [
  {
    "id": 1,
    "name": "Alex Rivera",
    "contact": "(312) 555-0142",
    "zips": [
      "60452",
      "60453",
      "60462",
      "60463",
      "60477"
    ]
  },
  {
    "id": 2,
    "name": "Morgan Patel",
    "contact": "(219) 555-0184",
    "zips": [
      "46307",
      "46373",
      "46375",
      "46385"
    ]
  },
  {
    "id": 3,
    "name": "Sam Chen",
    "contact": "(773) 555-0111",
    "zips": [
      "60608",
      "60616",
      "60609",
      "60632",
      "60623",
      "60638"
    ]
  },
  {
    "id": 4,
    "name": "Jamie Nguyen",
    "contact": "(847) 555-0190",
    "zips": [
      "60007",
      "60008",
      "60016",
      "60018",
      "60056",
      "60025"
    ]
  },
  {
    "id": 5,
    "name": "Taylor Brooks",
    "contact": "(765) 555-0177",
    "zips": [
      "47905",
      "47906",
      "47909"
    ]
  }
]

html_template = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Service Coverage Planner</title>

  <!-- Leaflet + Leaflet.draw + Turf -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="anonymous">
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin="anonymous"></script>
  <link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css">
  <script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/@turf/turf@6/turf.min.js"></script>

  <style>
    :root{
      --bg:#0b1020;
      --panel:#11162a;
      --muted:#96a0b5;
      --text:#e5e7eb;
      --accent:#7dd3fc;
      --accent-2:#ffa94d;
      --accent-3:#ff6d00;
      --card:#0f152a;
      --border:#1f2a44;
      --error:#ef4444;
      --ok:#22c55e;
    }
    *{box-sizing:border-box}
    html, body { height:100%; margin:0; background:var(--bg); color:var(--text); font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji"; }
    .app { display:flex; height:100%; width:100%; }

    /* Sidebar (tech list) */
    .sidebar {
      width:360px; max-width:42vw; background:var(--panel); border-right:1px solid var(--border);
      display:flex; flex-direction:column; padding:16px 14px; gap:12px; overflow:auto;
    }
    .brand { display:flex; align-items:center; gap:10px; }
    .brand .logo { width:28px; height:28px; border-radius:8px; background:linear-gradient(135deg, var(--accent), #60a5fa); display:inline-block; }
    .brand h1 { font-size:16px; margin:0; letter-spacing:0.3px; }
    .search { display:flex; gap:8px; }
    .search input {
      width:100%; padding:10px 12px; border-radius:10px; border:1px solid var(--border); outline:none;
      background:var(--card); color:var(--text);
    }
    .tiny { color:var(--muted); font-size:12px; }

    .adder { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:10px 12px; display:flex; flex-direction:column; gap:8px; }
    .row { display:flex; gap:8px; }
    .row input, .row textarea {
      width:100%; padding:8px 10px; border-radius:8px; border:1px solid var(--border); outline:none;
      background:#0e1430; color:var(--text);
    }
    .row textarea { min-height:62px; resize:vertical; }

    .tech-card {
      background:var(--card); border:1px solid var(--border); border-radius:12px; padding:10px 12px; display:flex; flex-direction:column; gap:8px;
    }
    .tech-header { display:flex; align-items:center; justify-content:space-between; gap:8px; }
    .tech-name { font-weight:600; }
    .tech-actions { display:flex; gap:8px; }
    .btn {
      padding:6px 10px; border-radius:8px; border:1px solid var(--border); background:#121a34; color:var(--text);
      cursor:pointer; font-size:12px;
    }
    .btn:hover{ border-color:#2a3a62; background:#0e1530; }
    .btn-primary { background:linear-gradient(135deg,#38bdf8,#60a5fa); color:#0b1020; border:none; }
    .btn-danger { background:#1a0f12; border-color:#3a1620; color:#fecaca; }
    .btn-primary:hover{ filter:brightness(0.95); }

    .zip-section { border-top:1px solid var(--border); margin-top:6px; padding-top:6px; }
    .zip-toggle { display:flex; align-items:center; gap:8px; background:transparent; color:var(--text);
      border:none; cursor:pointer; padding:6px 2px; width:100%; text-align:left; }
    .zip-toggle .arrow { width:10px; height:10px; border-right:2px solid var(--muted); border-bottom:2px solid var(--muted);
      transform: rotate(45deg); transition: transform .15s ease; margin-left:4px; }
    .zip-section.collapsed .zip-toggle .arrow { transform: rotate(-45deg); }
    .zip-section.collapsed .zip-list { display:none; }
    .zip-list { display:flex; flex-wrap:wrap; gap:6px; margin-top:6px; }
    .zip-pill {
      padding:4px 6px; border-radius:999px; background:#0e1430; border:1px solid var(--border); color:#e9edf5; font-size:12px;
    }
    .pill-missing { background:#311619; border-color:#5b1f27; color:#fecaca; }

    /* Main area: header + map + selection panel */
    .main { flex:1; display:flex; flex-direction:column; }
    .topbar {
      height:56px; display:flex; align-items:center; justify-content:space-between; padding:0 16px;
      border-bottom:1px solid var(--border); background:var(--panel);
    }
    .topbar .title { font-size:14px; font-weight:600; }
    .topbar .tools { display:flex; gap:10px; }
    .topbar .tools .btn { background:#101831; }

    .content { position:relative; flex:1; display:flex; }
    #map { flex:1; }
    .selection-panel {
      position:absolute; top:10px; right:10px; z-index:9999; background:rgba(17,22,42,0.96);
      border:1px solid var(--border); padding:12px; border-radius:12px; width:340px; max-height:70vh; overflow:auto;
      box-shadow:0 10px 30px rgba(0,0,0,0.45);
    }
    .selection-panel h3 { margin:0 0 8px 0; font-size:14px; }
    .selection-panel .small { color:var(--muted); font-size:12px; margin-bottom:6px; }
    .selection-panel ul { margin:8px 0 0 16px; padding:0; font-size:12px; }
    .selection-panel .btn { margin-top:8px; }

    /* Leaflet overrides for dark UI */
    .leaflet-control-layers { background:#0f152a !important; color:var(--text) !important; border:1px solid var(--border) !important; }
    .leaflet-container { background:#0a0f1f; }
    .leaflet-bar a, .leaflet-bar a:hover { background:#111a34; color:#fff; border-bottom:1px solid var(--border); }
    .leaflet-draw-toolbar { box-shadow:0 6px 18px rgba(0,0,0,.35); border-radius:8px; overflow:hidden; }
    .leaflet-draw-toolbar a { background:#111a34 !important; border:1px solid var(--border) !important; color:#e5e7eb !important; }
    .leaflet-draw-toolbar a:hover { background:#0e1530 !important; border-color:#2a3a62 !important; }
    .leaflet-draw-actions a { background:#0e1530 !important; color:#e5e7eb !important; border:1px solid var(--border) !important; }

    /* Rectangle icon inside the draw button (themed) */
    .leaflet-draw-draw-rectangle { position: relative; }
    .leaflet-draw-draw-rectangle::before {
      content: ""; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
      width: 16px; height: 12px; border: 2px solid var(--accent); border-radius: 2px;
      box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08); pointer-events: none;
    }
    .leaflet-draw-draw-rectangle:hover::before { border-color: #60a5fa; }

    /* Busy overlay */
    #busy { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
      background:rgba(17,22,42,0.96); border:1px solid var(--border); padding:10px 12px; border-radius:10px;
      z-index:10000; display:none; box-shadow:0 10px 30px rgba(0,0,0,.45) }
    @keyframes bl { 0%, 80%, 100% { opacity:.25 } 40% { opacity:1 } }

    /* Tech center labels (territory names) */
    .leaflet-marker-icon.tech-center-label { width:auto !important; height:auto !important; }
    .leaflet-marker-icon.tech-center-label img { width:auto !important; height:auto !important; }
    .tech-center-label, .tech-center-label * { pointer-events: none; }
    .tech-pill {
      display:inline-block; font-size:12px; font-weight:700; padding:2px 8px; border-radius:999px;
      background:rgba(10,15,25,0.85); color:#fff; border:2px solid currentColor;
      box-shadow:0 0 0 2px rgba(255,255,255,0.70); white-space:nowrap;
    }

    .legend { position:absolute; bottom:10px; left:10px; z-index:9999; background:rgba(17,22,42,0.96); border:1px solid var(--border); border-radius:10px; padding:8px 10px; font-size:12px; }
    a { color:var(--accent); text-decoration:none; }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <span class="logo"></span>
        <h1>Service Coverage Planner</h1>
      </div>

      <div class="search">
        <input id="techSearch" placeholder="Search technicians or ZIPs..." />
      </div>
      <div class="tiny">Click a tech to highlight their service area. Draw a rectangle on the map to list ZIPs and outline the union perimeter.</div>

      <div class="adder">
        <div class="row"><input id="addName" placeholder="Technician name" /></div>
        <div class="row"><input id="addContact" placeholder="Contact (optional)" /></div>
        <div class="row"><textarea id="addZips" placeholder="ZIPs (comma-separated) e.g. 60452,60453,60462"></textarea></div>
        <div class="row">
          <button id="addTech" class="btn-primary btn">Add Technician</button>
          <div id="addMsg" class="msg"></div>
        </div>
      </div>

      <div id="techList" class="tech-list"></div>
    </aside>

    <section class="main">
      <div class="topbar">
        <div class="title">Illinois & Indiana ZIP Coverage (USPS-aligned)</div>
        <div class="tools">
          <button id="clearAll" class="btn">Clear Highlights</button>
          <button id="toggleLabels" class="btn">Toggle Labels</button>
          <button id="toggleAllTerritories" class="btn">Show All Territories</button>
          <button id="resetTechs" class="btn">Reset Demo Data</button>
        </div>
      </div>
      <div class="content">
        <div id="map"></div>

        <div id="selectionPanel" class="selection-panel" hidden>
          <h3>Selected ZIPs</h3>
          <div class="small">Drag a rectangle to select an area on the map.</div>
          <ul id="zipList"></ul>
          <div class="row">
            <button id="copyZips" class="btn">Copy ZIPs</button>
            <button id="clearSelection" class="btn">Clear</button>
          </div>
          <div id="copyMsg" class="msg"></div>
        </div>

        <div id="busy">
          <span class="dot" style="display:inline-block;width:6px;height:6px;background:#7dd3fc;border-radius:50%;margin:0 2px;animation:bl 1.2s infinite"></span>
          <span class="dot" style="display:inline-block;width:6px;height:6px;background:#7dd3fc;border-radius:50%;margin:0 2px;animation:bl 1.2s infinite .15s"></span>
          <span class="dot" style="display:inline-block;width:6px;height:6px;background:#7dd3fc;border-radius:50%;margin:0 2px;animation:bl 1.2s infinite .3s"></span>
          <span id="busyMsg" style="margin-left:6px">Processing…</span>
        </div>

        <div class="legend" id="legendBox">
          <div><span style="display:inline-block;width:10px;height:10px;background:#8ecae6;border:1px solid #1d3557;margin-right:6px;"></span>ZIP polygons</div>
          <div><span style="display:inline-block;width:10px;height:3px;background:#ff6d00;margin-right:6px;"></span>Per-ZIP edges</div>
          <div><span style="display:inline-block;width:10px;height:3px;background:#d84315;margin-right:6px;"></span>Union perimeter</div>
        </div>
      </div>
    </section>
  </div>

  <script>
  // ------------------- Default technicians (injected from Python) -------------------
  /*__DEFAULT_TECHS__*/

  // State & persistence
  const STORAGE_KEY = "svc_techs_v1";
  let TECHS = [];
  function loadTechs() {
    try { const s = localStorage.getItem(STORAGE_KEY); if (s) { const arr = JSON.parse(s); if (Array.isArray(arr)) return arr; } } catch {}
    return DEFAULT_TECHS;
  }
  function saveTechs() { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(TECHS)); } catch {} }
  function resetTechs() { TECHS = DEFAULT_TECHS.slice(); saveTechs(); renderTechList(techSearch.value); if (allTerritoriesOn) buildAllTerritories(); }

  // ------------------- Map Setup -------------------
  const map = L.map("map", { zoomSnap: 0.5 }).setView([41.5, -88.0], 8);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
  }).addTo(map);

  const zipLayer = L.geoJSON(null, {
    style: () => ({ fillColor:"#8ecae6", color:"#2b344d", weight:0.6, fillOpacity:0.10 }),
    onEachFeature: (feature, layer) => {
      const p = feature.properties;
      layer.bindTooltip(`<b>${p.zip}</b> — ${p.city}, ${p.STATE}`, {direction:"top"});
    }
  }).addTo(map);

  const perZipEdges   = L.geoJSON(null, { style: { color:"#ff6d00", weight:3, fillOpacity:0 }}).addTo(map);
  const selectionFill = L.geoJSON(null, { style: { color:"#7dd3fc", weight:0, fillColor:"#7dd3fc", fillOpacity:0.05 }}).addTo(map);
  const selectionHalo = L.geoJSON(null, { style: { color:"#ffffff", weight:7, opacity:0.85, fillOpacity:0 }}).addTo(map);
  const unionOutline  = L.geoJSON(null, { style: { color:"#7dd3fc", weight:3, fillOpacity:0 }}).addTo(map);
  let selectionLabel  = null;
  let labelsLayer = L.layerGroup().addTo(map);
  let labelsEnabled = false;

  const drawControl = new L.Control.Draw({
    draw: { polygon:false, polyline:false, circle:false, marker:false, circlemarker:false,
      rectangle: { shapeOptions: { color:"#7dd3fc", weight:2 } } },
    edit: false
  });
  map.addControl(drawControl);

  // ------------------- Data Load (Esri Living Atlas) -------------------
  const BASE = "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/USA_ZIP_Code_Areas_anaylsis/FeatureServer/0/query";
  const IL_URL = BASE + "?where=STATE%20%3D%20'IL'&outFields=ZIP_CODE,PO_NAME,STATE&outSR=4326&f=geojson";
  const IN_URL = BASE + "?where=STATE%20%3D%20'IN'&outFields=ZIP_CODE,PO_NAME,STATE&outSR=4326&f=geojson";

  function normalizeFeature(f) {
    const p = f.properties || {};
    p.zip = p.zip || p.ZIP_CODE || "";
    p.city = p.city || p.PO_NAME || "";
    f.properties = { zip: p.zip, city: p.city, STATE: p.STATE || p.state || "" };
    return f;
  }

  let zipIndex = new Map();
  let allFeatures = [];
  let labelsBuilt = false;

  async function loadData() {
    const [il, _in] = await Promise.all([fetch(IL_URL).then(r=>r.json()), fetch(IN_URL).then(r=>r.json())]);
    const features = [...(il.features||[]), ...(_in.features||[])].map(normalizeFeature);
    allFeatures = features;

    zipLayer.addData({ type:"FeatureCollection", features });
    zipLayer.eachLayer(l => { const z = (l.feature.properties.zip||"").toString(); if (z) zipIndex.set(z, l); });

    const b = zipLayer.getBounds();
    if (b.isValid()) map.fitBounds(b, { padding:[20,20] });

    TECHS = loadTechs();
    renderTechList();
    if (allTerritoriesOn) buildAllTerritories();
  }
  loadData().catch(err => console.error("Data load failed", err));

  // ------------------- Labels on Zoom -------------------
  function buildLabels() {
    if (labelsBuilt) return;
    labelsBuilt = true;
    zipLayer.eachLayer(l => {
      const f = l.feature; if (!f) return;
      const center = turf.centerOfMass(f).geometry.coordinates;
      const zip = f.properties.zip;
      const icon = L.divIcon({ className:"zip-label", html:`<div style="font-size:10px;color:#0b132b;text-shadow:0 0 2px #fff">${zip}</div>` });
      const m = L.marker([center[1], center[0]], { icon });
      labelsLayer.addLayer(m);
    });
  }
  const LABEL_ZOOM = 12;
  function syncLabels() {
    if (map.getZoom() >= LABEL_ZOOM && labelsEnabled) { buildLabels(); if (!map.hasLayer(labelsLayer)) map.addLayer(labelsLayer); }
    else { if (map.hasLayer(labelsLayer)) map.removeLayer(labelsLayer); }
  }
  map.on("zoomend", syncLabels);
  document.getElementById("toggleLabels").addEventListener("click", () => {
    labelsEnabled = !labelsEnabled; syncLabels();
    document.getElementById("toggleLabels").textContent = labelsEnabled ? "Hide Labels" : "Show Labels";
  });

  // ------------------- Busy / perf helpers -------------------
  const unionCache = new Map();
  function showBusy(msg){ const el=document.getElementById('busy'); const m=document.getElementById('busyMsg'); if(m) m.textContent=msg||'Processing…'; if(el) el.style.display='block'; }
  function hideBusy(){ const el=document.getElementById('busy'); if(el) el.style.display='none'; }
  function dimBaseZips(){ zipLayer.setStyle({ color:"#3b4766", weight:0.4, fillOpacity:0.06 }); }
  function restoreBaseZips(){ zipLayer.setStyle({ color:"#2b344d", weight:0.6, fillOpacity:0.10 }); }

  async function unionMany(features, batch=40){
    if(!features.length) return null;
    let acc = features[0];
    for (let i=1;i<features.length;i++){
      try { acc = turf.union(acc, features[i]); } catch(e){ console.warn('union error', e); }
      if (i % batch === 0) await new Promise(r=>setTimeout(r));
    }
    return acc;
  }

  async function computeTechUnion(tech){
    const key = `${tech.id}:${tech.zips.join('|')}`;
    if (unionCache.has(key)) return unionCache.get(key);
    const feats = [];
    tech.zips.forEach(z => { const layer = zipIndex.get(z); if (layer) feats.push(layer.feature); });
    if (!feats.length) return null;
    showBusy(`Building ${tech.name}…`);
    let u = await unionMany(feats, 30);
    try { const tol = Math.min(0.002, 0.0006 + feats.length * 0.000004); u = turf.simplify(u, { tolerance: tol, highQuality: true }); } catch(e) {}
    unionCache.set(key, u);
    hideBusy();
    return u;
  }

  // ------------------- Rectangle Selection -------------------
  const selectionPanel = document.getElementById("selectionPanel");
  const zipListEl = document.getElementById("zipList");
  const clearSelectionBtn = document.getElementById("clearSelection");
  const copyZipsBtn = document.getElementById("copyZips");
  const copyMsg = document.getElementById("copyMsg");
  let lastSelectionZips = [];

  function clearSelectionLayers() {
    perZipEdges.clearLayers();
    selectionFill.clearLayers();
    selectionHalo.clearLayers();
    unionOutline.clearLayers();
    if (selectionLabel) { map.removeLayer(selectionLabel); selectionLabel = null; }
    zipListEl.innerHTML = "";
    selectionPanel.hidden = true;
    lastSelectionZips = [];
    if (copyMsg) { copyMsg.textContent = ""; copyMsg.className = "msg"; }
    if (!allTerritoriesOn) restoreBaseZips();
  }
  clearSelectionBtn.addEventListener("click", clearSelectionLayers);

  async function copySelectionZips(){
    if (!lastSelectionZips.length){ copyMsg.textContent = "No ZIPs to copy."; copyMsg.className="msg err"; return; }
    const text = lastSelectionZips.join(",");
    try { await navigator.clipboard.writeText(text); copyMsg.textContent = `Copied ${lastSelectionZips.length} ZIP${lastSelectionZips.length>1?"s":""} to clipboard.`; copyMsg.className="msg ok"; }
    catch(e){ try { const ta=document.createElement("textarea"); ta.value=text; document.body.appendChild(ta); ta.select(); document.execCommand("copy"); document.body.removeChild(ta); copyMsg.textContent = `Copied ${lastSelectionZips.length} ZIP${lastSelectionZips.length>1?"s":""} to clipboard.`; copyMsg.className="msg ok"; } catch(e2){ copyMsg.textContent="Copy failed."; copyMsg.className="msg err"; } }
  }
  copyZipsBtn.addEventListener("click", copySelectionZips);

  map.on(L.Draw.Event.CREATED, async e => {
    if (e.layerType !== "rectangle") return;
    const b = e.layer.getBounds();
    const rectPoly = turf.polygon([[
      [b.getWest(), b.getSouth()],
      [b.getEast(), b.getSouth()],
      [b.getEast(), b.getNorth()],
      [b.getWest(), b.getNorth()],
      [b.getWest(), b.getSouth()]
    ]]);

    const hits = [];
    showBusy('Selecting…');
    zipLayer.eachLayer(l => {
      const f = l.feature;
      const bb = l.getBounds ? l.getBounds() : null;
      if (bb) {
        if (bb.getEast() < b.getWest() || bb.getWest() > b.getEast() || bb.getNorth() < b.getSouth() || bb.getSouth() > b.getNorth()) return;
      }
      try { if (turf.booleanIntersects(f, rectPoly)) hits.push(f); } catch {}
    });

    zipListEl.innerHTML = "";
    const zips = Array.from(new Set(hits.map(h => h.properties.zip))).sort();
    lastSelectionZips = zips;
    hits.map(h => h.properties).sort((a,b)=>a.zip.localeCompare(b.zip)).forEach(p => {
      const li = document.createElement("li"); li.textContent = `${p.zip} — ${p.city} (${p.STATE})`; zipListEl.appendChild(li);
    });
    selectionPanel.hidden = hits.length === 0;
    if (copyMsg) { copyMsg.textContent = zips.length ? `Found ${zips.length} ZIP${zips.length>1?"s":""}.` : ""; copyMsg.className = zips.length ? "msg ok" : "msg"; }
    if (zips.length) dimBaseZips();

    perZipEdges.clearLayers();
    selectionFill.clearLayers(); selectionHalo.clearLayers(); unionOutline.clearLayers();
    if (selectionLabel) { map.removeLayer(selectionLabel); selectionLabel = null; }

    const edgeFeatures = [];
    const BIG = 180;
    if (hits.length <= BIG) {
      hits.forEach(f => { try { const line = turf.polygonToLine(f); if (line.type === "FeatureCollection") edgeFeatures.push(...line.features); else edgeFeatures.push(line); } catch {} });
      perZipEdges.addData({ type:"FeatureCollection", features: edgeFeatures });
    }

    if (hits.length) {
      showBusy(`Computing union (${hits.length} ZIPs)…`);
      let u = await unionMany(hits, 40);
      try { const tol = Math.min(0.002, 0.0006 + hits.length * 0.000004); u = turf.simplify(u, { tolerance: tol, highQuality: true }); } catch {}
      selectionFill.setStyle({ color:'#7dd3fc', fillColor:'#7dd3fc', weight:0, fillOpacity:0.05 });
      selectionFill.addData(u);
      try { const line = turf.polygonToLine(u); selectionHalo.addData(line); unionOutline.setStyle({ color: '#7dd3fc', weight:3, opacity:1 }); unionOutline.addData(line); }
      catch { selectionHalo.addData(u); unionOutline.setStyle({ color: '#7dd3fc', weight:3, opacity:1 }); unionOutline.addData(u); }
      try { const c = turf.centerOfMass(u).geometry.coordinates; const icon = L.divIcon({ className:'tech-center-label', iconSize: null, html:`<div class='tech-pill' style='color:#7dd3fc'>Selection (${zips.length})</div>` }); selectionLabel = L.marker([c[1], c[0]], { icon }).addTo(map); } catch {}
      const ub = unionOutline.getBounds(); if (ub.isValid()) map.fitBounds(ub, { padding:[20,20] });
    }
    hideBusy();
  });

  // ------------------- Technician CRUD + Interactions -------------------
  const techListEl = document.getElementById("techList");
  const techSearch = document.getElementById("techSearch");
  const addName = document.getElementById("addName");
  const addContact = document.getElementById("addContact");
  const addZips = document.getElementById("addZips");
  const addBtn = document.getElementById("addTech");
  const addMsg = document.getElementById("addMsg");
  const resetBtn = document.getElementById("resetTechs");

  function parseZips(text) {
    // Split on commas/whitespace, extract first 5-digit sequence from each token
    const uniq = Array.from(new Set(
      (text || "")
        .split(/[,\s]+/)
        .map(s => { const m = s.match(/\d{5}/); return m ? m[0] : null; })
        .filter(Boolean)
    )).sort();
    return uniq;
  }

  function addTech() {
    const name = addName.value.trim();
    const contact = addContact.value.trim();
    const zips = parseZips(addZips.value);
    if (!name) { addMsg.textContent = "Name is required."; addMsg.className = "msg err"; return; }
    if (!zips.length) { addMsg.textContent = "Enter at least one valid 5-digit ZIP."; addMsg.className = "msg err"; return; }
    const id = Date.now();
    TECHS.push({ id, name, contact, zips });
    saveTechs();
    addMsg.textContent = "Technician added."; addMsg.className = "msg ok";
    addName.value = ""; addContact.value = ""; addZips.value = "";
    renderTechList(techSearch.value);
    if (allTerritoriesOn) buildAllTerritories();
  }
  addBtn.addEventListener("click", addTech);
  resetBtn.addEventListener("click", resetTechs);
  document.getElementById("clearAll").addEventListener("click", () => { clearSelectionLayers(); clearTechHighlight(); });

  async function highlightTechArea(tech) {
    const feats = [];
    tech.zips.forEach(z => { const layer = zipIndex.get(z); if (layer) feats.push(layer.feature); });

    // Draw per-zip edges (skip for huge)
    perZipEdges.clearLayers();
    const edgeFeatures = [];
    const BIG = 180;
    if (feats.length && feats.length <= BIG) {
      feats.forEach(f => { try { const line = turf.polygonToLine(f); if (line.type === "FeatureCollection") edgeFeatures.push(...line.features); else edgeFeatures.push(line); } catch {} });
      perZipEdges.addData({ type:"FeatureCollection", features: edgeFeatures });
    }

    // Compute union (cached + simplified) and draw fill+halo+outline+label
    selectionFill.clearLayers(); selectionHalo.clearLayers(); unionOutline.clearLayers();
    if (selectionLabel) { map.removeLayer(selectionLabel); selectionLabel = null; }
    showBusy(`Building ${tech.name}…`);
    const u = await computeTechUnion(tech);
    hideBusy();
    if (!u) return;
    const idx = TECHS.findIndex(x => x.id === tech.id);
    const color = COLORS[(idx >= 0 ? idx : 0) % COLORS.length];

    selectionFill.setStyle({ color: color, fillColor: color, weight:0, fillOpacity:0.05 });
    selectionFill.addData(u);

    try { const line = turf.polygonToLine(u); selectionHalo.addData(line); unionOutline.setStyle({ color: color, weight:3, opacity:1 }); unionOutline.addData(line); }
    catch { selectionHalo.addData(u); unionOutline.setStyle({ color: color, weight:3, opacity:1 }); unionOutline.addData(u); }

    try { const c = turf.centerOfMass(u).geometry.coordinates; const icon = L.divIcon({ className:"tech-center-label", iconSize: null, html:`<div class="tech-pill" style="color:${color}">${tech.name}</div>` }); selectionLabel = L.marker([c[1], c[0]], { icon }).addTo(map); } catch {}

    dimBaseZips();
    const ub = unionOutline.getBounds(); if (ub.isValid()) map.fitBounds(ub, { padding:[20,20] });
  }

  function clearTechHighlight() {
    perZipEdges.clearLayers();
    selectionFill.clearLayers();
    selectionHalo.clearLayers();
    unionOutline.clearLayers();
    if (selectionLabel) { map.removeLayer(selectionLabel); selectionLabel = null; }
    if (!allTerritoriesOn) restoreBaseZips();
  }

  function renderTechList(filter="") {
    techListEl.innerHTML = "";
    const q = filter ? filter.trim().toLowerCase() : "";
    TECHS.forEach(t => {
      const matches = !q || t.name.toLowerCase().includes(q) || t.zips.some(z => z.includes(q));
      if (!matches) return;

      const card = document.createElement("div"); card.className = "tech-card";
      const header = document.createElement("div"); header.className = "tech-header";
      const name = document.createElement("div"); name.className = "tech-name"; name.textContent = t.name;
      const actions = document.createElement("div"); actions.className = "tech-actions";
      const btnView = document.createElement("button"); btnView.className = "btn-primary btn"; btnView.textContent = "View Area";
      const btnEdit = document.createElement("button"); btnEdit.className = "btn"; btnEdit.textContent = "Edit";
      const btnDelete = document.createElement("button"); btnDelete.className = "btn btn-danger"; btnDelete.textContent = "Delete";
      actions.appendChild(btnView); actions.appendChild(btnEdit); actions.appendChild(btnDelete);
      header.appendChild(name); header.appendChild(actions);
      card.appendChild(header);

      if (t.contact) { const contact = document.createElement("div"); contact.className = "tiny"; contact.textContent = t.contact; card.appendChild(contact); }

      // Collapsible ZIP section
      const zipSection = document.createElement("div"); zipSection.className = "zip-section collapsed";
      const zipToggle = document.createElement("button"); zipToggle.className = "zip-toggle"; zipToggle.setAttribute("aria-expanded","false");
      zipToggle.innerHTML = `<span class="arrow"></span><span>ZIPs</span> <span class="tiny">(${t.zips.length})</span>`;
      const zipWrap = document.createElement("div"); zipWrap.className = "zip-list";
      t.zips.forEach(z => { const pill = document.createElement("span"); pill.className = "zip-pill"; pill.textContent = z; if (!zipIndex.has(z)) pill.classList.add("pill-missing"); zipWrap.appendChild(pill); });
      zipSection.appendChild(zipToggle); zipSection.appendChild(zipWrap); card.appendChild(zipSection);
      zipToggle.addEventListener("click", () => { const isCollapsed = zipSection.classList.toggle("collapsed"); zipToggle.setAttribute("aria-expanded", String(!isCollapsed)); });

      // Inline edit panel
      const edit = document.createElement("div"); edit.className = "edit-panel"; edit.style.display="none"; edit.style.gap="8px";
      const inName = document.createElement("input"); inName.placeholder = "Name"; inName.value = t.name;
      const inContact = document.createElement("input"); inContact.placeholder = "Contact"; inContact.value = t.contact || "";
      const inZips = document.createElement("textarea"); inZips.placeholder = "ZIPs (comma-separated)"; inZips.value = t.zips.join(",");
      const rowA = document.createElement("div"); rowA.className = "row"; rowA.appendChild(inName);
      const rowB = document.createElement("div"); rowB.className = "row"; rowB.appendChild(inContact);
      const rowC = document.createElement("div"); rowC.className = "row"; rowC.appendChild(inZips);
      const rowD = document.createElement("div"); rowD.className = "row";
      const btnSave = document.createElement("button"); btnSave.className = "btn-primary btn"; btnSave.textContent = "Save";
      const btnCancel = document.createElement("button"); btnCancel.className = "btn"; btnCancel.textContent = "Cancel";
      const msg = document.createElement("div"); msg.className = "msg"; msg.style.alignSelf = "center";
      rowD.appendChild(btnSave); rowD.appendChild(btnCancel); rowD.appendChild(msg);
      edit.appendChild(rowA); edit.appendChild(rowB); edit.appendChild(rowC); edit.appendChild(rowD);
      card.appendChild(edit);

      // Handlers
      btnView.addEventListener("click", () => highlightTechArea(t));
      btnEdit.addEventListener("click", () => { edit.style.display = (edit.style.display === "none" ? "flex" : "none"); msg.textContent = ""; });
      btnCancel.addEventListener("click", () => { edit.style.display = "none"; inName.value = t.name; inContact.value = t.contact || ""; inZips.value = t.zips.join(","); msg.textContent = ""; });
      btnSave.addEventListener("click", () => {
        const newName = inName.value.trim();
        const newContact = inContact.value.trim();
        const newZips = parseZips(inZips.value);
        if (!newName) { msg.textContent = "Name is required."; msg.className="msg err"; return; }
        if (!newZips.length) { msg.textContent = "Enter at least one valid 5-digit ZIP."; msg.className="msg err"; return; }
        t.name = newName; t.contact = newContact; t.zips = newZips;
        saveTechs();
        msg.textContent = "Saved."; msg.className="msg ok";
        renderTechList(techSearch.value);
        if (allTerritoriesOn) buildAllTerritories();
      });
      btnDelete.addEventListener("click", () => {
        if (!confirm(`Delete ${t.name}?`)) return;
        TECHS = TECHS.filter(x => x.id !== t.id);
        saveTechs();
        renderTechList(techSearch.value);
        if (allTerritoriesOn) buildAllTerritories();
      });

      techListEl.appendChild(card);
    });
  }

  techSearch.addEventListener("input", e => renderTechList(e.target.value));

  // ------------------- All Territories Overlay (multi-view) -------------------
  const COLORS = ["#e11d48","#22c55e","#3b82f6","#a855f7","#f59e0b","#ec4899","#14b8a6","#f97316","#84cc16","#06b6d4","#8b5cf6","#ef4444"];
  let allTerritoriesOn = false;
  const allTechOverlays = L.layerGroup();

  async function buildAllTerritories(){
    showBusy("Building territories…");
    allTechOverlays.clearLayers();
    const legend = document.getElementById("legendBox");
    const old = document.getElementById("territoryLegend"); if (old) old.remove();
    const lg = document.createElement("div"); lg.id = "territoryLegend"; lg.style.marginTop = "6px";
    lg.innerHTML = "<div style='margin-bottom:4px;font-weight:600'>Territories</div>";

    for (let idx=0; idx<TECHS.length; idx++){
      const t = TECHS[idx];
      const u = await computeTechUnion(t);
      if (!u) continue;
      const color = COLORS[idx % COLORS.length];

      try { L.geoJSON(u, { style: { color, weight:0, fillColor: color, fillOpacity: 0.05 } }).addTo(allTechOverlays); } catch(e){}
      let halo = null;
      try { const line = turf.polygonToLine(u); halo = L.geoJSON(line, { style: { color:"#ffffff", weight:7, opacity:0.85, lineJoin:"round", lineCap:"round" } }); }
      catch(e){ halo = L.geoJSON(u, { style: { color:"#ffffff", weight:7, opacity:0.85, lineJoin:"round", lineCap:"round" } }); }
      halo.addTo(allTechOverlays);
      let outline = null;
      try { const line = turf.polygonToLine(u); outline = L.geoJSON(line, { style: { color, weight:3, opacity:1, lineJoin:"round", lineCap:"round" } }); }
      catch(e){ outline = L.geoJSON(u, { style: { color, weight:3, opacity:1, lineJoin:"round", lineCap:"round" } }); }
      outline.addTo(allTechOverlays);

      try { const c = turf.centerOfMass(u).geometry.coordinates; const icon = L.divIcon({ className:"tech-center-label", iconSize: null, html:`<div class="tech-pill" style="color:${color}">${t.name}</div>` }); L.marker([c[1], c[0]], { icon }).addTo(allTechOverlays); } catch(e) {}

      const row = document.createElement("div"); row.style.display = "flex"; row.style.alignItems = "center"; row.style.gap = "6px"; row.style.marginTop = "4px";
      row.innerHTML = `<span style="display:inline-block;width:12px;height:3px;background:${color};border-radius:2px;"></span><span>${t.name}</span>`;
      lg.appendChild(row);
      await new Promise(r=>setTimeout(r));
    }
    legend.appendChild(lg);
    if (!map.hasLayer(allTechOverlays)) allTechOverlays.addTo(map);
    dimBaseZips();
    hideBusy();
  }

  function clearAllTerritories(){
    allTechOverlays.clearLayers();
    if (map.hasLayer(allTechOverlays)) map.removeLayer(allTechOverlays);
    const old = document.getElementById("territoryLegend"); if (old) old.remove();
    restoreBaseZips();
  }

  const toggleAllBtn = document.getElementById("toggleAllTerritories");
  toggleAllBtn.addEventListener("click", async () => {
    allTerritoriesOn = !allTerritoriesOn;
    if (allTerritoriesOn) { await buildAllTerritories(); toggleAllBtn.textContent = "Hide All Territories"; }
    else { clearAllTerritories(); toggleAllBtn.textContent = "Show All Territories"; }
  });
  </script>
</body>
</html>
"""

def main():
    default_json = "const DEFAULT_TECHS = " + json.dumps(DEFAULT_TECHS, ensure_ascii=False) + ";"
    html = html_template.replace("/*__DEFAULT_TECHS__*/", default_json)
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT.resolve()}")

if __name__ == "__main__":
    main()
