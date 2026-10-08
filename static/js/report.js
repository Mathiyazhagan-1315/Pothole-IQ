const pe = $("#pick"), pm = basemap("pick", +pe.dataset.lat, +pe.dataset.lng, 14);
let pin = null, pos = null, busy = false;
function setPin(lat, lng) {
  pos = { lat, lng };
  if (pin) pin.setLatLng([lat, lng]); else pin = L.marker([lat, lng]).addTo(pm);
  $("#coord").textContent = `Pinned: ${lat.toFixed(5)}, ${lng.toFixed(5)}`;
}
pm.on("click", e => setPin(e.latlng.lat, e.latlng.lng));
$("#gps").onclick = () => {
  if (!navigator.geolocation) return toast("Location is not available. Tap the map instead.");
  navigator.geolocation.getCurrentPosition(p => { setPin(p.coords.latitude, p.coords.longitude); pm.setView([p.coords.latitude, p.coords.longitude], 17); },
    () => toast("Could not get your location. Tap the map instead."), { enableHighAccuracy: true, timeout: 10000 });
};
$("#drop").onclick = () => $("#photo").click();
$("#photo").onchange = async e => {
  const f = e.target.files[0]; if (!f) return;
  if (f.size > 8 * 1024 * 1024) { e.target.value = ""; return toast("Photo is over 8 MB. Choose a smaller one."); }
  $("#preview").src = URL.createObjectURL(f); $("#preview").hidden = false; $("#droptxt").hidden = true;
  const ai = $("#ai"); ai.hidden = false; ai.textContent = "AI is analysing the photo…";
  try {
    const fd = new FormData(); fd.append("photo", f);
    const r = await api("/api/analyze", { method: "POST", body: fd });
    ai.innerHTML = `<b>AI severity:</b> ${pill(r.label, r.label)} <b>${r.score}</b>/100
      <div class="meter"><i style="width:${r.score}%"></i></div><span class="hint">Method: ${esc(r.method)}${r.detail.reason ? " · " + esc(r.detail.reason) : ""}${r.detail.note ? " · " + esc(r.detail.note) : ""}</span>`;
  } catch (err) { ai.textContent = err.message; }
};
$("#form").onsubmit = async e => {
  e.preventDefault(); if (busy) return;
  if (!pos) return toast("Please tap the map to pin the pothole location.");
  if (!$("#photo").files[0]) return toast("Please add a photo so AI can rate the damage.");
  busy = true; const b = $("#submit"); b.disabled = true; b.textContent = "Submitting…";
  try {
    const fd = new FormData(); fd.append("lat", pos.lat); fd.append("lng", pos.lng);
    fd.append("road_name", $("#road").value); fd.append("description", $("#desc").value); fd.append("photo", $("#photo").files[0]);
    const r = await api("/api/reports", { method: "POST", body: fd }), x = r.report;
    const out = $("#result"); out.hidden = false;
    out.innerHTML = `<b>${r.merged ? "Already reported nearby. We added your report to it." : "Thank you! Report received."}</b><br>
      Severity ${pill(x.severity_label, x.severity_label)} · Priority ${pill(x.priority.level, LEVELS[x.priority.level])} · Risk ${x.risk}/100 · ${x.report_count} report(s)<br>
      <a href="/dashboard">See the repair queue →</a> &nbsp; <a href="/">View live map →</a>`;
    $("#form").reset(); $("#preview").hidden = true; $("#droptxt").hidden = false; $("#ai").hidden = true;
    toast(r.merged ? "Merged with existing report" : "Report submitted");
    out.scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (err) { toast(err.message); }
  finally { busy = false; b.disabled = false; b.textContent = "Submit report"; }
};
