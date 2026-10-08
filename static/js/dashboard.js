let pin = sessionStorage.getItem("pin") || "";
const hdr = () => ({ "Content-Type": "application/json", "X-Authority-Pin": pin });
const NEXT = { open: ["in_progress", "Start"], in_progress: ["fixed", "Mark fixed"] };
function renderLock() { $("#unlock").textContent = pin ? "🔓 Authority mode on" : "🔒 Authority mode"; }
async function unlock() {
  if (pin) { pin = ""; sessionStorage.removeItem("pin"); renderLock(); return load(); }
  const p = prompt("Enter authority PIN"); if (!p) return;
  try { await api("/api/authority/check", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pin: p }) });
    pin = p; sessionStorage.setItem("pin", p); renderLock(); toast("Authority mode enabled"); load(); }
  catch (e) { toast("Wrong PIN"); }
}
async function setStatus(id, status) {
  try { await api(`/api/reports/${id}`, { method: "PATCH", headers: hdr(), body: JSON.stringify({ status }) }); toast("Updated"); load(); }
  catch (e) { toast(e.message); }
}
async function load() {
  const q = rainQS($("#rain").value), qs = q ? "?" + q : "";
  $("#csv").href = "/api/export.csv" + qs;
  const [s, rows] = await Promise.all([api("/api/stats" + qs), api("/api/queue" + qs)]);
  $("#stats").innerHTML = [["Open", s.open, ""], ["Fix now", s.fix_now, "hot"], ["Severe", s.severe, "hot"], ["Avg risk", s.avg_risk, ""], ["Duplicates merged", s.duplicates_merged, ""], ["Fixed", s.fixed, ""]]
    .map(([l, v, c]) => `<div class="stat ${c}"><b>${v}</b><span>${l}</span></div>`).join("");
  const max = Math.max(1, ...Object.values(s.by_severity));
  $("#bars").innerHTML = ["severe", "moderate", "minor"].map(k => `<div class="bar"><span>${k}</span><div><i style="width:${s.by_severity[k] / max * 100}%;background:${COLORS[k]}"></i></div><b>${s.by_severity[k]}</b></div>`).join("");
  $("#empty").hidden = rows.length > 0;
  $("#tbl tbody").innerHTML = rows.map(r => {
    const p = r.priority.parts, tot = Math.max(1, r.priority.score), n = NEXT[r.status];
    return `<tr><td><b>${r.rank}</b></td><td><b>${esc(r.road_name || "Unnamed road")}</b><br><small class="hint">${esc(r.why)}</small></td>
    <td>${pill(r.severity_label, r.severity_label)} ${r.severity_score}</td><td>${r.report_count}</td><td>${r.risk}</td>
    <td>${pill(r.priority.level, LEVELS[r.priority.level])} <b>${r.priority.score}</b>
      <div class="stack" title="Severity ${p.severity} · Risk ${p.risk} · Reports ${p.reports} · Age ${p.age}">${[["s1", p.severity], ["s2", p.risk], ["s3", p.reports], ["s4", p.age]].map(([c, v]) => `<i class="${c}" style="width:${v / tot * 100}%"></i>`).join("")}</div></td>
    <td>${pin && n ? `<button class="btn sm" onclick="setStatus(${r.id},'${n[0]}')">${n[1]}</button>` : `<span class="hint">${r.status.replace("_", " ")}</span>`}</td></tr>`;
  }).join("");
}
$("#unlock").onclick = unlock;
$("#rain").oninput = e => { $("#rainval").textContent = rainLabel(e.target.value); load(); };
renderLock(); load().catch(e => toast(e.message));
