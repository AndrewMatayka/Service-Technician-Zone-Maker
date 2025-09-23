(function(){
  function ready(){
    var map = window[window._MAP];
    var zipLayer = window[window._LAYER];
    var labels = window[window._LABELS];
    if(!map || !zipLayer || !labels || !window.turf){ return setTimeout(ready,50); }

    // 1) Labels only at high zoom (add/remove entire layer for perf)
    function syncLabels(){
      var show = map.getZoom() >= window._LABEL_ZOOM;
      if(show && !map.hasLayer(labels)) map.addLayer(labels);
      if(!show && map.hasLayer(labels)) map.removeLayer(labels);
    }
    map.on('zoomend', syncLabels);
    map.whenReady(syncLabels); syncLabels();

    // 2) Click-to-select single ZIP (persistent)
    var selected = null;
    function resetFillOutline(layer){ layer.setStyle({weight:1,color:'#1d3557',fillOpacity:0.15}); }
    zipLayer.eachLayer(function(l){
      l.on('click', function(){
        if(selected && selected !== l) resetFillOutline(selected);
        selected = l;
        l.setStyle({weight:4,color:'#ff3d00',fillOpacity:0.25});
        if(l.bringToFront) l.bringToFront();
      });
    });

    // 3) Rectangle selection → list ZIPs, outline each ZIP, and draw union perimeter
    var rectHighlighted = [];   // polygon layers we touched
    var perZipEdges = null;     // L.geoJSON of per-ZIP boundaries
    var unionOutline = null;    // L.geoJSON of union perimeter

    function clearSelection(){
      rectHighlighted.forEach(resetFillOutline);
      rectHighlighted = [];
      if(perZipEdges){ map.removeLayer(perZipEdges); perZipEdges = null; }
      if(unionOutline){ map.removeLayer(unionOutline); unionOutline = null; }
      var list=document.getElementById('zip-list');
      var panel=document.getElementById('zip-results');
      if(list) list.innerHTML='';
      if(panel) panel.hidden=true;
    }

    function showPanel(items){
      var list=document.getElementById('zip-list');
      var panel=document.getElementById('zip-results');
      if(!list || !panel) return;
      list.innerHTML='';
      items.sort(function(a,b){ return a.zip.localeCompare(b.zip); });
      items.forEach(function(it){
        var li=document.createElement('li');
        li.textContent = it.zip + ' — ' + it.city + ' (' + it.state + ')';
        list.appendChild(li);
      });
      panel.hidden = items.length===0;
    }

    function drawPerZipEdges(items){
      if(perZipEdges){ map.removeLayer(perZipEdges); perZipEdges = null; }
      if(!items.length) return;
      var edgeFeatures = [];
      for(var i=0;i<items.length;i++){
        try{
          var line = turf.polygonToLine(items[i].feature);
          if(line.type==='FeatureCollection'){ edgeFeatures = edgeFeatures.concat(line.features); }
          else { edgeFeatures.push(line); }
        }catch(e){ console.warn('polygonToLine failed for ZIP', items[i].zip, e); }
      }
      perZipEdges = L.geoJSON({type:'FeatureCollection',features:edgeFeatures},{style:{color:'#ff6d00',weight:3,fillOpacity:0}}).addTo(map);
    }

    function drawUnionPerimeter(items){
      if(unionOutline){ map.removeLayer(unionOutline); unionOutline = null; }
      if(!items.length) return;
      var maxUnion=400;
      var features = items.slice(0,maxUnion).map(function(it){ return it.feature; });
      var u = features[0];
      for(var i=1;i<features.length;i++){
        try{ u = turf.union(u, features[i]); }
        catch(e){ console.warn('Union failed at i=',i,e); break; }
      }
      try{
        var outer = turf.polygonToLine(u);
        unionOutline = L.geoJSON(outer,{style:{color:'#d84315',weight:5,fillOpacity:0}}).addTo(map);
      }catch(e){
        unionOutline = L.geoJSON(u,{style:{color:'#d84315',weight:5,fillOpacity:0}}).addTo(map);
      }
    }

    map.on(L.Draw.Event.CREATED, function(e){
      if(e.layerType!=='rectangle') return;
      var b=e.layer.getBounds();
      var rectPoly=turf.polygon([[
        [b.getWest(), b.getSouth()],
        [b.getEast(), b.getSouth()],
        [b.getEast(), b.getNorth()],
        [b.getWest(), b.getNorth()],
        [b.getWest(), b.getSouth()]
      ]]);

      var hits=[];
      zipLayer.eachLayer(function(l){
        var f=l.feature; if(!f) return;
        var bb = l.getBounds ? l.getBounds() : null;
        if(bb){
          if(bb.getEast()<b.getWest() || bb.getWest()>b.getEast() ||
             bb.getNorth()<b.getSouth() || bb.getSouth()>b.getNorth()){ return; }
        }
        try{
          if(turf.booleanIntersects(f,rectPoly)){
            // subtle style on underlying fills
            l.setStyle({weight:2,color:'#607d8b',fillOpacity:0.08});
            if(l.bringToFront) l.bringToFront();
            hits.push({
              layer:l, feature:f,
              zip:(f.properties.zip||f.properties.ZIP_CODE||''),
              city:(f.properties.city||f.properties.PO_NAME||''),
              state:(f.properties.STATE||'')
            });
          }
        }catch(err){ console.warn('Intersect check failed', err); }
      });

      clearSelection();
      rectHighlighted = hits.map(function(h){ return h.layer; });
      showPanel(hits);
      drawPerZipEdges(hits);
      drawUnionPerimeter(hits);
    });

    var clearBtn=document.getElementById('zip-clear');
    if(clearBtn) clearBtn.onclick = clearSelection;
  }
  setTimeout(ready,0);
})();