#!/usr/bin/env python3
# IL+IN USPS-aligned ZIPs with rectangle selection → per-ZIP boundaries + union perimeter
# No triple-quoted strings; JS goes to an external file (zip_select.js)

import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import Draw
from pathlib import Path

# ---------------------- SETTINGS ----------------------
LABEL_ZOOM   = 12   # labels appear at this zoom or higher (raise to 13 in dense areas)
SIMPLIFY_TOL = 0.0  # 0.0 = no simplification (highest fidelity)
CLEAN_GEOM   = True # run buffer(0) to fix minor topology issues
OUT_HTML     = "zip_map_il_in_select.html"
OUT_JS       = "zip_select.js"
# ------------------------------------------------------

BASE = ("https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_ZIP_Code_Areas_anaylsis/FeatureServer/0/query")
IL_URL = f"{BASE}?where=STATE%20%3D%20'IL'&outFields=ZIP_CODE,PO_NAME,STATE&outSR=4326&f=geojson"
IN_URL = f"{BASE}?where=STATE%20%3D%20'IN'&outFields=ZIP_CODE,PO_NAME,STATE&outSR=4326&f=geojson"

def load_state(url: str) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(url)
    gdf = gdf[["ZIP_CODE", "PO_NAME", "STATE", "geometry"]].rename(
        columns={"ZIP_CODE": "zip", "PO_NAME": "city"}
    )
    if gdf.crs:
        gdf = gdf.to_crs(epsg=4326)
    if CLEAN_GEOM:
        try:
            gdf["geometry"] = gdf.buffer(0)  # fix tiny self-intersections
        except Exception:
            pass
    if SIMPLIFY_TOL > 0:
        gdf["geometry"] = gdf.geometry.simplify(SIMPLIFY_TOL, preserve_topology=True)
    return gdf

# Load data
gdf_il = load_state(IL_URL)
gdf_in = load_state(IN_URL)
gdf    = gpd.GeoDataFrame(pd.concat([gdf_il, gdf_in], ignore_index=True), crs="EPSG:4326")

# ---------------------- MAP ----------------------
m = folium.Map(location=(41.5, -88.0), zoom_start=8, tiles="cartodbpositron")

def base_style(_):
    return {"fillColor": "#8ecae6", "color": "#1d3557", "weight": 1, "fillOpacity": 0.15}

def hover_style(_):
    return {"weight": 3, "color": "#e67e22", "fillOpacity": 0.20}

gj = folium.GeoJson(
    data=gdf.__geo_interface__,
    name="ZIP Boundaries (USPS-aligned)",
    style_function=base_style,
    highlight_function=hover_style,
    tooltip=folium.features.GeoJsonTooltip(
        fields=["zip", "city", "STATE"], aliases=["ZIP", "City", "State"], sticky=True
    ),
).add_to(m)

# Fit to IL + IN
minx, miny, maxx, maxy = gdf.total_bounds
m.fit_bounds([[miny, minx], [maxy, maxx]])

# ---- Labels (separate layer; toggled by zoom) ----
label_group = folium.FeatureGroup(name="ZIP Labels", show=False).add_to(m)
reps = gdf.copy()
reps["rep"] = reps.geometry.representative_point()
for _, r in reps.iterrows():
    folium.Marker(
        [r["rep"].y, r["rep"].x],
        icon=folium.DivIcon(
            class_name="zip-label",
            html=f"<div style='font-size:9pt;color:#0b132b;text-shadow:0 0 2px #fff;white-space:nowrap;'>{r['zip']}</div>",
        ),
    ).add_to(label_group)

folium.LayerControl(collapsed=False).add_to(m)

# ---- Draw control (rectangle only) ----
Draw(
    export=False,
    position="topleft",
    draw_options={
        "polyline": False, "polygon": False, "circle": False,
        "circlemarker": False, "marker": False, "rectangle": True,
    },
    edit_options={"edit": False, "remove": True},
).add_to(m)

# ---- Side panel (built without triple quotes) ----
panel_html_lines = [
    "<style>",
    "#zip-results{position:absolute;top:10px;right:10px;z-index:9999;",
    "background:rgba(255,255,255,0.96);padding:10px 12px;border-radius:8px;",
    "box-shadow:0 6px 20px rgba(0,0,0,0.15);max-width:320px;max-height:50vh;overflow:auto;",
    "font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial;}",
    "#zip-results h4{margin:0 0 6px 0;font-size:14px;}",
    "#zip-results .small{color:#555;font-size:11px;margin-bottom:6px;}",
    "#zip-results ul{margin:6px 0 0 16px;padding:0;font-size:12px;}",
    "#zip-results button{margin-top:7px;padding:6px 8px;border:1px solid #ddd;",
    "background:#f6f7f9;border-radius:6px;cursor:pointer;}",
    "</style>",
    "<div id='zip-results' hidden>",
    "  <h4>Selected ZIPs</h4>",
    "  <div class='small'>Drag a rectangle to select.</div>",
    "  <ul id='zip-list'></ul>",
    "  <button id='zip-clear'>Clear selection</button>",
    "</div>",
]
m.get_root().html.add_child(folium.Element("\n".join(panel_html_lines)))

# ---- Tiny inline script to expose variable names for external JS ----
map_var    = m.get_name()
layer_var  = gj.get_name()
labels_var = label_group.get_name()

setup_js = (
    "<script>"
    f"window._MAP='{map_var}';"
    f"window._LAYER='{layer_var}';"
    f"window._LABELS='{labels_var}';"
    f"window._LABEL_ZOOM={LABEL_ZOOM};"
    "</script>"
)
# Turf (for geometry ops), then our external JS
m.get_root().html.add_child(folium.Element("<script src='https://cdn.jsdelivr.net/npm/@turf/turf@6/turf.min.js'></script>"))
m.get_root().html.add_child(folium.Element(setup_js))
m.get_root().html.add_child(folium.Element("<script src='zip_select.js'></script>"))

# ---- Save HTML now (so we know where to write JS) ----
m.save(OUT_HTML)

# ---- Write external JS (no triple quotes) ----
js_lines = [
"(function(){",
"  function ready(){",
"    var map = window[window._MAP];",
"    var zipLayer = window[window._LAYER];",
"    var labels = window[window._LABELS];",
"    if(!map || !zipLayer || !labels || !window.turf){ return setTimeout(ready,50); }",
"",
"    // 1) Labels only at high zoom (add/remove entire layer for perf)",
"    function syncLabels(){",
"      var show = map.getZoom() >= window._LABEL_ZOOM;",
"      if(show && !map.hasLayer(labels)) map.addLayer(labels);",
"      if(!show && map.hasLayer(labels)) map.removeLayer(labels);",
"    }",
"    map.on('zoomend', syncLabels);",
"    map.whenReady(syncLabels); syncLabels();",
"",
"    // 2) Click-to-select single ZIP (persistent)",
"    var selected = null;",
"    function resetFillOutline(layer){ layer.setStyle({weight:1,color:'#1d3557',fillOpacity:0.15}); }",
"    zipLayer.eachLayer(function(l){",
"      l.on('click', function(){",
"        if(selected && selected !== l) resetFillOutline(selected);",
"        selected = l;",
"        l.setStyle({weight:4,color:'#ff3d00',fillOpacity:0.25});",
"        if(l.bringToFront) l.bringToFront();",
"      });",
"    });",
"",
"    // 3) Rectangle selection → list ZIPs, outline each ZIP, and draw union perimeter",
"    var rectHighlighted = [];   // polygon layers we touched",
"    var perZipEdges = null;     // L.geoJSON of per-ZIP boundaries",
"    var unionOutline = null;    // L.geoJSON of union perimeter",
"",
"    function clearSelection(){",
"      rectHighlighted.forEach(resetFillOutline);",
"      rectHighlighted = [];",
"      if(perZipEdges){ map.removeLayer(perZipEdges); perZipEdges = null; }",
"      if(unionOutline){ map.removeLayer(unionOutline); unionOutline = null; }",
"      var list=document.getElementById('zip-list');",
"      var panel=document.getElementById('zip-results');",
"      if(list) list.innerHTML='';",
"      if(panel) panel.hidden=true;",
"    }",
"",
"    function showPanel(items){",
"      var list=document.getElementById('zip-list');",
"      var panel=document.getElementById('zip-results');",
"      if(!list || !panel) return;",
"      list.innerHTML='';",
"      items.sort(function(a,b){ return a.zip.localeCompare(b.zip); });",
"      items.forEach(function(it){",
"        var li=document.createElement('li');",
"        li.textContent = it.zip + ' — ' + it.city + ' (' + it.state + ')';",
"        list.appendChild(li);",
"      });",
"      panel.hidden = items.length===0;",
"    }",
"",
"    function drawPerZipEdges(items){",
"      if(perZipEdges){ map.removeLayer(perZipEdges); perZipEdges = null; }",
"      if(!items.length) return;",
"      var edgeFeatures = [];",
"      for(var i=0;i<items.length;i++){",
"        try{",
"          var line = turf.polygonToLine(items[i].feature);",
"          if(line.type==='FeatureCollection'){ edgeFeatures = edgeFeatures.concat(line.features); }",
"          else { edgeFeatures.push(line); }",
"        }catch(e){ console.warn('polygonToLine failed for ZIP', items[i].zip, e); }",
"      }",
"      perZipEdges = L.geoJSON({type:'FeatureCollection',features:edgeFeatures},{style:{color:'#ff6d00',weight:3,fillOpacity:0}}).addTo(map);",
"    }",
"",
"    function drawUnionPerimeter(items){",
"      if(unionOutline){ map.removeLayer(unionOutline); unionOutline = null; }",
"      if(!items.length) return;",
"      var maxUnion=400;",
"      var features = items.slice(0,maxUnion).map(function(it){ return it.feature; });",
"      var u = features[0];",
"      for(var i=1;i<features.length;i++){",
"        try{ u = turf.union(u, features[i]); }",
"        catch(e){ console.warn('Union failed at i=',i,e); break; }",
"      }",
"      try{",
"        var outer = turf.polygonToLine(u);",
"        unionOutline = L.geoJSON(outer,{style:{color:'#d84315',weight:5,fillOpacity:0}}).addTo(map);",
"      }catch(e){",
"        unionOutline = L.geoJSON(u,{style:{color:'#d84315',weight:5,fillOpacity:0}}).addTo(map);",
"      }",
"    }",
"",
"    map.on(L.Draw.Event.CREATED, function(e){",
"      if(e.layerType!=='rectangle') return;",
"      var b=e.layer.getBounds();",
"      var rectPoly=turf.polygon([[",
"        [b.getWest(), b.getSouth()],",
"        [b.getEast(), b.getSouth()],",
"        [b.getEast(), b.getNorth()],",
"        [b.getWest(), b.getNorth()],",
"        [b.getWest(), b.getSouth()]",
"      ]]);",
"",
"      var hits=[];",
"      zipLayer.eachLayer(function(l){",
"        var f=l.feature; if(!f) return;",
"        var bb = l.getBounds ? l.getBounds() : null;",
"        if(bb){",
"          if(bb.getEast()<b.getWest() || bb.getWest()>b.getEast() ||",
"             bb.getNorth()<b.getSouth() || bb.getSouth()>b.getNorth()){ return; }",
"        }",
"        try{",
"          if(turf.booleanIntersects(f,rectPoly)){",
"            // subtle style on underlying fills",
"            l.setStyle({weight:2,color:'#607d8b',fillOpacity:0.08});",
"            if(l.bringToFront) l.bringToFront();",
"            hits.push({",
"              layer:l, feature:f,",
"              zip:(f.properties.zip||f.properties.ZIP_CODE||''),",
"              city:(f.properties.city||f.properties.PO_NAME||''),",
"              state:(f.properties.STATE||'')",
"            });",
"          }",
"        }catch(err){ console.warn('Intersect check failed', err); }",
"      });",
"",
"      clearSelection();",
"      rectHighlighted = hits.map(function(h){ return h.layer; });",
"      showPanel(hits);",
"      drawPerZipEdges(hits);",
"      drawUnionPerimeter(hits);",
"    });",
"",
"    var clearBtn=document.getElementById('zip-clear');",
"    if(clearBtn) clearBtn.onclick = clearSelection;",
"  }",
"  setTimeout(ready,0);",
"})();",
]
Path(OUT_JS).write_text("\n".join(js_lines), encoding="utf-8")

print(f"Map saved to {OUT_HTML}\nWrote helper JS to {OUT_JS}\nOpen the HTML in a browser with {OUT_JS} in the same folder.")
