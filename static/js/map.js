const el = $("#map"), map = basemap("map", +el.dataset.lat, +el.dataset.lng), layer = L.layerGroup().addTo(map), markers = {};
function popup(r) {
  return `<b>${esc(r.road_name || "Unnamed road")}</b><br>${pill(r.severity_label, r.severity_label)} ${pill(r.priority.level, LEVELS[r.priority.level])}<br>
  Risk <b>${r.risk}</b>/100 · Reports <b>${r.report_count}</b> · Status ${esc(r.status.replace("_", " "))}<br><small>${esc(r.why)}</small>
  ${r.description ? `<br><small>${esc(r.description)}</small>` : ""}${r.photo ? `<img src="${r.photo}" alt="Pothole photo">` : ""}`;
}
async function load() {
  const qs = rainQS($("#rain").value);
  const items = await api("/api/reports" + (qs ? "?" + qs : ""));
  layer.clearLayers();
  items.filter(r => r.status !== "fixed").forEach(r => {
    L.circle([r.lat, r.lng], { radius: 40 + r.risk * 3.2, color: COLORS.severe, weight: 0, fillOpacity: Math.min(.5, r.risk / 200) }).addTo(layer);
    const m = L.circleMarker([r.lat, r.lng], { radius: 7 + r.report_count * .8, color: "#fff", weight: 2, fillColor: COLORS[r.severity_label], fillOpacity: 1 }).bindPopup(popup(r)).addTo(layer);
    markers[r.id] = m;
  });
  const top = items.filter(r => r.status !== "fixed").sort((a, b) => b.priority.score - a.priority.score).slice(0, 5);
  $("#top").innerHTML = top.length ? top.map((r, i) => `<li data-id="${r.id}"><b>${i + 1}. ${esc(r.road_name || "Unnamed road")}</b> ${pill(r.priority.level, LEVELS[r.priority.level])}<small>Priority ${r.priority.score} · Risk ${r.risk} · ${r.report_count} report(s)</small></li>`).join("") : "<li>No open reports yet.</li>";
  $("#top").querySelectorAll("li[data-id]").forEach(li => li.onclick = () => { const m = markers[li.dataset.id]; map.setView(m.getLatLng(), 16); m.openPopup(); });
}
$("#rain").oninput = e => { $("#rainval").textContent = rainLabel(e.target.value); load(); };
api(`/api/rain?lat=${el.dataset.lat}&lng=${el.dataset.lng}`).then(r => {
  $("#rainnow").textContent = `Past 3 days ${r.past_3d_mm} mm · next 2 days ${r.next_2d_mm} mm (${r.source})`;
}).catch(() => {});
load().catch(e => toast(e.message));
