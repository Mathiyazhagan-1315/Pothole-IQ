const $ = (s, el = document) => el.querySelector(s);
const COLORS = { minor: "#22c55e", moderate: "#f59e0b", severe: "#ef4444" };
const LEVELS = { fix_now: "Fix now", soon: "Soon", monitor: "Monitor", fixed: "Fixed" };
function toast(msg) { const t = $("#toast"); t.textContent = msg; t.classList.add("show"); setTimeout(() => t.classList.remove("show"), 2800); }
async function api(url, opts = {}) {
  const r = await fetch(url, opts); let d = {};
  try { d = await r.json(); } catch (e) {}
  if (!r.ok) throw new Error(d.error || "Something went wrong. Please try again.");
  return d;
}
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pill = (cls, txt) => `<span class="pill ${cls}">${txt}</span>`;
function rainQS(v) { return Number(v) >= 0 ? `rain=${v}` : ""; }
function rainLabel(v) { return Number(v) < 0 ? "Live weather" : `${v} mm simulated`; }
function basemap(el, lat, lng, z = 13) {
  const m = L.map(el).setView([lat, lng], z);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "© OpenStreetMap" }).addTo(m);
  return m;
}
