/* 世界遊記：地圖、標記、路線、搜尋、面板。資料來自 data/wiki.json（build.py 產生）。 */
(function () {
  "use strict";
  var P = window.PAGE || {}, ROOT = window.ROOT || "";

  // 深淺色切換
  document.getElementById("theme").addEventListener("click", function () {
    var cur = document.documentElement.dataset.theme ||
      (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    var next = cur === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("theme", next); } catch (e) {}
  });

  // 面板收合（桌機：往左收；手機：三段高度）
  var panel = document.getElementById("panel");
  var mobile = matchMedia("(max-width: 767px)");
  document.getElementById("toggle").addEventListener("click", function () {
    if (mobile.matches) {
      if (panel.classList.contains("collapsed")) panel.classList.remove("collapsed");
      else if (panel.classList.contains("expanded")) { panel.classList.remove("expanded"); panel.classList.add("collapsed"); }
      else panel.classList.add("expanded");
    } else panel.classList.toggle("collapsed");
    setTimeout(function () { map.invalidateSize(); }, 300);
  });

  var map = L.map("map", { zoomControl: false, worldCopyJump: true }).setView([35, 60], 3);
  L.control.zoom({ position: "bottomright" }).addTo(map);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);

  // 地圖可視範圍要避開面板
  function pad() {
    if (mobile.matches) return { paddingTopLeft: [20, 70], paddingBottomRight: [20, innerHeight * 0.47] };
    if (panel.classList.contains("collapsed")) return { paddingTopLeft: [40, 80], paddingBottomRight: [40, 40] };
    return { paddingTopLeft: [460, 80], paddingBottomRight: [40, 40] };
  }

  fetch(ROOT + "data/wiki.json").then(function (r) { return r.json(); }).then(draw);

  function visitFor(p) {
    var v = p.visits || [];
    if (P.trip) {
      var mine = v.filter(function (x) { return x.trip === P.trip; });
      if (P.day) {
        var d = mine.filter(function (x) { return x.day === P.day; });
        if (d.length) return d[0];
      }
      if (mine.length) return mine[0];
    }
    // 沒指定旅程：優先顯示已發生的造訪
    var order = ["visited/as-planned", "visited/moved", "visited/added", "visited/unconfirmed",
      "planned/unconfirmed", "planned/skipped", "planned/upcoming", "planned/dropped"];
    function k(x) { return order.indexOf(x.status + "/" + x.detail); }
    return v.slice().sort(function (a, b) { return k(a) - k(b); })[0] || {};
  }

  // 類別圖示（24×24，白色填滿；在 CSS 裡用 currentColor 換色）
  var ICON = {
    landmark: "M6 3h2v18H6zM8 4h11l-3 4 3 4H8z",
    religious: "M2 4h20v3H2zM4.5 9h15v2.5h-15zM6 7h2.5v14H6zM15.5 7H18v14h-2.5z",
    museum: "M12 2 2 7.5h20zM4 9h16v2H4zM5 12h2.5v6H5zM9.5 12H12v6H9.5zM14 12h2.5v6H14zM16.5 12H19v6h-2.5zM3 19h18v2.5H3z",
    nature: "M1.5 20.5 9 6l4.2 7.6L16 9l6.5 11.5z",
    viewpoint: "M12 5C6 5 1.5 12 1.5 12S6 19 12 19s10.5-7 10.5-7S18 5 12 5zm0 11.2a4.2 4.2 0 1 1 0-8.4 4.2 4.2 0 0 1 0 8.4zm0-2.2a2 2 0 1 0 0-4 2 2 0 0 0 0 4z",
    food: "M6 2h1.6v6.5h1.2V2h1.6v6.5h1.2V2h1.6v7.2a3 3 0 0 1-2.6 3V22H8.4v-9.8A3 3 0 0 1 6 9.2zM16.5 2C18.6 2 20 4.6 20 8.5c0 2.7-1 4.3-2.2 4.8V22h-2.2V2z",
    shopping: "M5 8h14l1.2 14H3.8zM8.5 8V6.5a3.5 3.5 0 0 1 7 0V8h-2V6.5a1.5 1.5 0 0 0-3 0V8z",
    activity: "M12 1.8 15.1 8l6.9.9-5 4.9 1.2 6.9L12 17.4l-6.2 3.3L7 13.8 2 8.9 8.9 8z",
    station: "M7 2h10a4 4 0 0 1 4 4v9a3.5 3.5 0 0 1-2.6 3.4L20.5 22h-2.6l-2-3.3H8.1L6.1 22H3.5l2.1-3.6A3.5 3.5 0 0 1 3 15V6a4 4 0 0 1 4-4zm-1 4.5v4.5h12V6.5zm1.5 7a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm9 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3z",
    transport: "M21.5 15.5v-2.2L13.5 8.5V3.6a1.5 1.5 0 0 0-3 0v4.9l-8 4.8v2.2l8-2.4v5.2l-2.2 1.6V22l3.7-1 3.7 1v-2.1l-2.2-1.6v-5.2z",
    "lodging-area": "M2 6h2.5v8h17v-3.5A3.5 3.5 0 0 0 18 7h-7v6H8.5V9.5a2.5 2.5 0 1 0-4 0V6zM2 15h20v5h-2.5v-2.5h-15V20H2z"
  };
  function svg(cat) {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" fill-rule="evenodd" d="' +
      (ICON[cat] || ICON.landmark) + '"/></svg>';
  }
  // status 大類決定大小（visited 大、planned 小），detail 小類決定樣式與角標
  var BADGE = { moved: "改", added: "+", unconfirmed: "?", skipped: "×" };
  document.querySelectorAll(".legend .pin[data-cat]").forEach(function (el) {
    el.insertAdjacentHTML("afterbegin", svg(el.getAttribute("data-cat")));
  });

  function draw(D) {
    var trips = D.trips, stz = D.status_zh, cz = D.cat_zh, cc = D.cat_color;
    var placesL = L.layerGroup(), stationsL = L.layerGroup(), planL = L.layerGroup(), actualL = L.layerGroup(),
      regionsL = L.layerGroup(), plannedL = L.layerGroup(), plannedRegionsL = L.layerGroup(), planToggle = L.layerGroup();
    var visitedInView = 0, fitB = P.fit ? L.latLngBounds(P.fit) : null;
    var only = P.only ? new Set(P.only) : null;
    var tripPage = P.type === "trip" || P.type === "day";

    D.places.forEach(function (p) {
      if (p.lat == null) return;
      var v = visitFor(p);
      if (v.detail === "dropped") return;
      if (only && !only.has(p.slug)) return;
      if (tripPage && !(p.visits || []).some(function (x) { return x.trip === P.trip; })) return;
      var big = v.status === "visited", dt = v.detail || "upcoming", isStation = p.category === "station";
      var done = big && dt !== "unconfirmed";
      // 大小：visited 大、planned 小；車站一律小一號
      var size = big ? (isStation ? 20 : 30) : (dt === "skipped" ? 16 : (isStation ? 14 : 20));
      var badge = BADGE[dt] ? '<b class="pin-badge b-' + dt + '">' + BADGE[dt] + "</b>" : "";
      var icon = L.divIcon({
        className: "", iconSize: [size, size], iconAnchor: [size / 2, size / 2],
        html: '<div class="pin ' + (done ? "done" : "s-" + dt) + (isStation ? " stn" : "") +
          (P.type === "place" && p.slug !== P.slug ? " dim" : "") + '" style="--c:' + (cc[p.category] || "#555") +
          ";width:" + size + "px;height:" + size + 'px">' + svg(p.category) + badge + "</div>"
      });
      var date = v.actual || v.planned || "";
      var html = "<b>" + p.title + "</b><br><span class='pp-s'>" + (cz[p.category] || "") +
        (v.status ? " · " + stz[v.status + "/" + v.detail] : "") + (date ? " · " + date : "") + "</span>" +
        (p.lines && p.lines.length ? "<br><span class='pp-s'>" + p.lines.join("、") + "</span>" : "") +
        (p.thumb ? "<img src='" + ROOT + p.thumb + "' alt=''>" : "") +
        "<br><a href='" + ROOT + p.url + "'>看全文</a>";
      // 計畫的（planned）放進「計畫」圖層，預設不顯示；景點頁自己那個點例外
      var target = (!big && p.slug !== P.slug) ? plannedL : (isStation ? stationsL : placesL);
      if (big && (!fitB || fitB.contains([p.lat, p.lng]))) visitedInView++;
      L.marker([p.lat, p.lng], { icon: icon, title: p.title, zIndexOffset: done ? 200 : (isStation ? -100 : 0) })
        .bindPopup(html).addTo(target);
    });

    // 行政區大圓：有圖片用圖片，沒有就寫字；去過的實心，只有計畫的空心
    var PALETTE = ["#5d4037", "#c2185b", "#1565c0", "#00897b", "#6a1b9a", "#ef6c00", "#2e7d32", "#37474f", "#ad1457", "#283593"];
    (D.regions || []).forEach(function (r, i) {
      if (r.lat == null || !r.places) return;
      if (tripPage && r.trips.indexOf(P.trip) < 0) return;
      var color = r.color || PALETTE[i % PALETTE.length];   // 顏色由 build.py 決定，和國家頁的卡片一致
      var inner = r.icon ? '<img src="' + ROOT + r.icon + '" alt="">' : "<span>" + r.label + "</span>";
      var icon = L.divIcon({
        className: "", iconSize: [52, 52], iconAnchor: [26, 26],
        html: '<div class="region-wrap"><a class="region' + (r.visited ? " done" : "") + (r.label.length > 2 ? " long" : "") +
          '" style="--c:' + color + '" href="' + ROOT + r.url + '" title="' + r.title + '">' + inner + "</a></div>"
      });
      L.marker([r.lat, r.lng], { icon: icon, title: r.title, zIndexOffset: 1000, keyboard: false })
        .addTo(r.visited ? regionsL : plannedRegionsL);
    });

    // 國家標記（世界縮放 zoom ≤ 4）：國旗＋國名，點了進國家頁
    var countriesL = L.layerGroup();
    (D.countries || []).forEach(function (c) {
      if (c.lat == null) return;
      var flag = c.flag ? '<img src="' + ROOT + c.flag + '" alt="">' : "<i>" + c.cc + "</i>";
      L.marker([c.lat, c.lng], {
        icon: L.divIcon({ className: "", iconSize: null, iconAnchor: [0, 0],
          html: '<a class="country' + (c.visited ? " done" : "") + '" href="' + ROOT + c.url + '">' + flag + "<span>" + c.name + "</span></a>" }),
        title: c.name, zIndexOffset: 1100, keyboard: false
      }).addTo(countriesL);
    });

    // 迷霧地圖（9.4）：全世界蓋一層霧，去過的行政區挖洞「解鎖」；收錄國家的行政區畫邊界
    var fogL = L.layerGroup();
    map.createPane("fog").style.zIndex = 350;   // 在圖磚之上、路線與標記之下
    fetch(ROOT + "data/boundaries.json").then(function (r) { return r.ok ? r.json() : null; }).then(function (B) {
      if (!B) return;
      var holes = [], ll = function (ring) { return ring.map(function (p) { return [p[1], p[0]]; }); };
      B.features.forEach(function (f) {
        var pr = f.properties;
        if (pr.visited) f.geometry.coordinates.forEach(function (poly) { holes.push(ll(poly[0])); });
        L.geoJSON(f, { pane: "fog", interactive: false, style: pr.visited
          ? { color: pr.color || "#444", weight: 2, opacity: 0.9, fill: false }
          : { color: "#ffffff", weight: 1, opacity: 0.7, fill: false } }).addTo(fogL);
      });
      L.polygon([[[-85, -540], [85, -540], [85, 540], [-85, 540]]].concat(holes), {
        pane: "fog", interactive: false, stroke: false, fillColor: "#5f6b75", fillOpacity: 0.45
      }).addTo(fogL);
    });

    Object.keys(D.routes).forEach(function (t) {
      if (tripPage && t !== P.trip) return;
      var color = (trips[t] || {}).color || "#666";
      D.routes[t].forEach(function (d) {
        if (P.type === "day" && d.day !== P.day) return;
        if (d.plan.length > 1)
          L.polyline(d.plan, { color: color, weight: 2.5, dashArray: "6 7", opacity: 0.85 })
            .bindTooltip("計畫：第 " + d.day + " 天").addTo(planL);
        if (d.actual.length)
          L.polyline(d.actual, d.actual_kind === "sketch"
            ? { color: color, weight: 3.5, opacity: 0.75, dashArray: "1 6", lineCap: "round" }
            : { color: color, weight: 3.5, opacity: 0.75 })
            .bindTooltip("實際：第 " + d.day + " 天" + ({ gpx: "（GPX）", sketch: "（依手繪路線重建，非 GPS）" }[d.actual_kind] || ""))
            .on("click", function () { location.href = ROOT + d.url; }).addTo(actualL);
      });
    });

    // 計畫（planned 景點、計畫路線、只有計畫的行政區）預設隱藏，勾選才顯示。
    // 例外：畫面範圍內一個去過的地方都沒有（例如還沒出發的旅程），就自動顯示計畫。
    var planOn = visitedInView === 0;
    actualL.addTo(map);
    fogL.addTo(map);
    if (planOn) planToggle.addTo(map);
    // 勾選框只代表使用者的選擇（用空的 toggle 圖層），實際顯示哪一層由縮放決定
    var regionT = L.layerGroup().addTo(map), placeT = L.layerGroup().addTo(map), stationT = L.layerGroup().addTo(map);
    L.control.layers(null, {
      "國家／都道府縣／縣市／州": regionT, "景點": placeT, "車站": stationT,
      "實際路線（實線）": actualL, "計畫（景點、虛線路線）": planToggle,
      "迷霧（去過的行政區才解鎖）": fogL
    }, { position: "topright", collapsed: mobile.matches }).addTo(map);

    // 縮放分工（9.4）：zoom ≤ 4 只顯示國家（國旗）；5～8 顯示行政區大圓；zoom ≥ 9 才顯示景點與車站的小圈圈。
    // 日程頁、景點頁本來就是看景點：小圈圈一直顯示，不顯示大圓。
    var SPLIT = 8, WORLD = 4, always = P.type === "day" || P.type === "place";
    var userOn = new Map([[regionT, true], [placeT, true], [stationT, true]]), syncing = false;
    var toggleOf = new Map([[countriesL, regionT], [regionsL, regionT], [plannedRegionsL, regionT],
      [placesL, placeT], [plannedL, placeT], [planL, placeT], [stationsL, stationT]]);
    map.on("overlayadd overlayremove", function (e) {
      if (syncing) return;
      if (userOn.has(e.layer)) userOn.set(e.layer, e.type === "overlayadd");
      if (e.layer === planToggle) planOn = e.type === "overlayadd";
      syncZoom();
    });
    function want(layer, show, follow) {
      show = show && userOn.get(toggleOf.get(layer));
      if (show && !map.hasLayer(layer)) map.addLayer(layer);
      if (!show && map.hasLayer(layer)) map.removeLayer(layer);
    }
    function syncZoom() {
      var z = map.getZoom();
      syncing = true;
      want(countriesL, !always && z <= WORLD, regionsL);
      want(regionsL, !always && z > WORLD && z <= SPLIT);
      want(placesL, always || z > SPLIT);
      want(stationsL, always || z > SPLIT);
      want(plannedRegionsL, planOn && !always && z > WORLD && z <= SPLIT, regionsL);
      want(plannedL, planOn && (always || z > SPLIT), placesL);
      want(planL, planOn, placesL);
      syncing = false;
      // 大圓隨縮放變大變小，避免全部疊在一起
      map.getContainer().dataset.zb = z <= 5 ? "s" : (z <= 6 ? "m" : "l");
    }
    map.on("zoomend", syncZoom);

    if (P.center && P.center[0] != null) map.setView(P.center, P.zoom || 12);
    else if (P.fit) map.fitBounds(P.fit, Object.assign({ maxZoom: 15 }, pad()));
    else {
      var all = D.places.filter(function (p) { return p.lat != null; }).map(function (p) { return [p.lat, p.lng]; });
      if (all.length) map.fitBounds(all, Object.assign({ maxZoom: 6 }, pad()));
    }
    if (P.type === "place" && !mobile.matches && !panel.classList.contains("collapsed")) map.panBy([-210, 0], { animate: false });
    syncZoom();

    search(D);
    album(D.photos || []);
  }

  // 相簿：點照片 → 放大檢視（左右切換、Esc 關閉），地圖同時飛到拍照的景點（9.7）
  function album(ph) {
    if (!ph.length) return;
    var box = document.createElement("div");
    box.className = "lb"; box.hidden = true;
    box.innerHTML = '<button class="lb-x" type="button" aria-label="關閉">×</button>' +
      '<button class="lb-nav lb-prev" type="button" aria-label="上一張">‹</button>' +
      '<figure><img alt=""><figcaption></figcaption></figure>' +
      '<button class="lb-nav lb-next" type="button" aria-label="下一張">›</button>';
    document.body.appendChild(box);
    var img = box.querySelector("img"), cap = box.querySelector("figcaption"), cur = 0, ping = null;
    function show(i) {
      cur = (i + ph.length) % ph.length;
      var p = ph[cur];
      img.src = ROOT + p.src; img.alt = p.title;
      cap.innerHTML = "<b>" + p.title + "</b><span>" + [p.country, p.region, p.date].filter(Boolean).join(" · ") +
        "</span><a href='" + ROOT + p.url + "'>看景點頁</a><small>" + (cur + 1) + " / " + ph.length + "</small>";
      box.hidden = false;
      box.classList.toggle("single", ph.length < 2);
      if (p.lat != null) {
        map.flyTo([p.lat, p.lng], Math.max(map.getZoom(), 14), { duration: 1.2 });
        if (ping) map.removeLayer(ping);
        ping = L.marker([p.lat, p.lng], { icon: L.divIcon({ className: "", iconSize: [44, 44], iconAnchor: [22, 22],
          html: '<div class="ping"></div>' }), interactive: false, zIndexOffset: 2000 }).addTo(map);
      }
    }
    function close() { box.hidden = true; if (ping) { map.removeLayer(ping); ping = null; } }
    box.querySelector(".lb-x").onclick = close;
    box.querySelector(".lb-prev").onclick = function () { show(cur - 1); };
    box.querySelector(".lb-next").onclick = function () { show(cur + 1); };
    document.addEventListener("keydown", function (e) {
      if (box.hidden) return;
      if (e.key === "Escape") close();
      else if (e.key === "ArrowLeft") show(cur - 1);
      else if (e.key === "ArrowRight") show(cur + 1);
    });
    document.addEventListener("click", function (e) {
      var t = e.target.closest("[data-photo]");
      if (t) { e.preventDefault(); show(+t.getAttribute("data-photo")); return; }
      // 景點頁的照片也可以點開
      var im = e.target.closest(".wiki img");
      if (im) {
        var src = im.getAttribute("src") || "", i = ph.findIndex(function (p) { return src.indexOf(p.src) >= 0; });
        if (i >= 0) { e.preventDefault(); show(i); }
      }
    });
  }

  // 搜尋（中文名、原名、slug）
  function search(D) {
    var q = document.getElementById("q"), ul = document.getElementById("results");
    q.addEventListener("input", function () {
      var s = q.value.trim().toLowerCase();
      ul.innerHTML = "";
      if (!s) { ul.hidden = true; return; }
      var hits = D.places.filter(function (p) {
        return p.title.toLowerCase().indexOf(s) >= 0 || p.slug.indexOf(s) >= 0;
      }).slice(0, 10);
      hits.forEach(function (p) {
        var li = document.createElement("li");
        li.innerHTML = "<a href='" + ROOT + p.url + "'>" + p.title + "<small>" + (D.cat_zh[p.category] || "") + "</small></a>";
        ul.appendChild(li);
      });
      if (!hits.length) ul.innerHTML = "<li><a>找不到</a></li>";
      ul.hidden = false;
    });
    document.addEventListener("click", function (e) { if (!e.target.closest(".search")) ul.hidden = true; });
  }
})();
