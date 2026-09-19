const DNI = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek"];
const min = s => +s.slice(0,2)*60 + +s.slice(3,5);
const T0 = min(OS_CZASU.od), T1 = min(OS_CZASU.do); // oś z dane/<rok>-zajecia.yaml

// ===================== KONFLIKTY (liczone z danych) =====================
const konflikty = [];
for (let i = 0; i < ZAJECIA.length; i++)
  for (let j = i+1; j < ZAJECIA.length; j++) {
    const a = ZAJECIA[i], b = ZAJECIA[j];
    if (a.dzien === b.dzien && min(a.od) < min(b.do) && min(b.od) < min(a.do))
      konflikty.push([a, b]);
  }
const wKonflikcie = new Set(konflikty.flat());
document.getElementById("confN").textContent = konflikty.length ? `(${konflikty.length})` : "";

const esc = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;");
const flagTxt = z => z.flagi.length ? " · " + z.flagi.join(" · ") : "";

// ===================== KALENDARZ =====================
(function renderCal() {
  const root = document.getElementById("calRoot");
  let html = '<div class="cal-axis"><div></div><div class="axis-track">';
  for (let t = T0; t <= T1 - 30; t += 60)
    html += `<span style="left:${(t-T0)/(T1-T0)*100}%">${Math.floor(t/60)}:00</span>`;
  html += "</div></div>";

  for (const d of DNI) {
    const items = ZAJECIA.filter(z => z.dzien === d);
    // proste szeregowanie w pionie: nakładające się bloki idą do kolejnych "pasów"
    const lanes = [];
    for (const z of items.sort((x,y) => min(x.od) - min(y.od))) {
      let l = 0;
      while (lanes[l] && lanes[l].some(o => min(o.od) < min(z.do) && min(z.od) < min(o.do))) l++;
      (lanes[l] = lanes[l] || []).push(z);
      z._lane = l;
    }
    const laneH = 52, pad = 8;
    const h = Math.max(64, lanes.length * laneH + pad*2);
    html += `<div class="cal-day"><div class="dname">${d}</div>` +
            `<div class="day-track${items.length ? "" : " empty"}" style="height:${h}px">`;
    for (let t = T0; t <= T1; t += 15)
      html += `<div class="gridline${t % 60 === 0 ? " hour" : ""}" style="left:${(t-T0)/(T1-T0)*100}%"></div>`;
    for (const z of items) {
      const l = (min(z.od)-T0)/(T1-T0)*100, wPct = (min(z.do)-min(z.od))/(T1-T0)*100;
      const cls = `blk ${z.forma.toLowerCase()}${wKonflikcie.has(z) ? " conflict" : ""}`;
      const fl = z.flagi.includes("25/26") ? ' <span class="fl">⚠️</span>' : "";
      const przed = z.przedmiot ? `${esc(z.przedmiot)} — ` : "";
      const forma = { W:"wykład", C:"ćwiczenia", K:"konsultacje" }[z.forma];
      html += `<div class="${cls}" tabindex="0" role="button" aria-expanded="false" style="left:${l}%;width:${wPct}%;top:${pad + z._lane*laneH}px;height:${laneH-8}px" ` +
              `title="${esc(z.kier)}${z.przedmiot ? " · " + esc(z.przedmiot) : ""} (${z.forma}) ${z.od}–${z.do}, s. ${esc(z.sala)}${esc(flagTxt(z))}">` +
              `<b>${esc(z.kier)}${fl} <span class="sala">s. ${esc(z.sala)}</span></b><span class="t">${z.od}–${z.do}</span>` +
              `<span class="more">${przed}${forma}${z.grupy !== "-" ? "<br>" + esc(z.grupy) : ""}` +
              `${z.flagi.length ? "<br>" + esc(z.flagi.join(" · ")) : ""}</span></div>`;
    }
    html += "</div></div>";
  }
  root.innerHTML = html;

  // rozwijanie bloku po kliknięciu (krótkie zajęcia się nie mieszczą)
  const zwin = wyjatek => root.querySelectorAll(".blk.open").forEach(b => {
    if (b !== wyjatek) { b.classList.remove("open"); b.setAttribute("aria-expanded", "false"); }
  });
  const przelacz = b => {
    zwin(b);
    b.setAttribute("aria-expanded", String(b.classList.toggle("open")));
  };
  root.addEventListener("click", e => { const b = e.target.closest(".blk"); if (b) przelacz(b); });
  root.addEventListener("keydown", e => {
    const b = e.target.closest(".blk");
    if (b && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); przelacz(b); }
  });
  document.addEventListener("click", e => { if (!e.target.closest(".blk")) zwin(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") zwin(); });
})();

// ===================== LISTA =====================
(function renderList() {
  const root = document.getElementById("listRoot");
  let html = "";
  for (const d of DNI) {
    const items = ZAJECIA.filter(z => z.dzien === d).sort((x,y) => min(x.od) - min(y.od));
    if (!items.length) continue;
    html += `<h3>${d}</h3>`;
    for (const z of items) {
      html += `<div class="lrow${wKonflikcie.has(z) ? " conflict" : ""}">` +
        `<span class="time">${z.od}–${z.do}</span>` +
        `<span class="forma ${z.forma.toLowerCase()}">${z.forma}</span>` +
        `<span><b>${esc(z.kier)}</b>${z.przedmiot ? " — " + esc(z.przedmiot) : ""}<br>` +
        `<span class="meta">sala ${esc(z.sala)} · ${esc(z.grupy)}${esc(flagTxt(z))}</span></span></div>`;
    }
  }
  root.innerHTML = html;
})();

// ===================== TABELA =====================
(function renderTbl() {
  let html = '<table><thead><tr><th>Dzień</th><th>Od</th><th>Do</th><th>Kierunek</th><th>Przedmiot</th><th>Forma</th><th>Sala</th><th>Grupy</th><th>Uwagi</th><th>Źródło</th></tr></thead><tbody>';
  for (const z of ZAJECIA)
    html += `<tr><td>${z.dzien}</td><td>${z.od}</td><td>${z.do}</td><td>${esc(z.kier)}</td>` +
            `<td>${esc(z.przedmiot)}</td><td>${z.forma}</td><td>${esc(z.sala)}</td>` +
            `<td>${esc(z.grupy)}</td><td class="uw">${esc(z.flagi.join(", "))}</td>` +
            `<td class="uw">${esc(z.zrodlo || "")}</td></tr>`;
  document.getElementById("tblRoot").innerHTML = html + "</tbody></table>";
})();

// ===================== KONFLIKTY (widok) =====================
(function renderConf() {
  const root = document.getElementById("confRoot");
  root.innerHTML = konflikty.length ? konflikty.map(([a,b]) => {
    const o0 = Math.max(min(a.od), min(b.od)), o1 = Math.min(min(a.do), min(b.do));
    const f = m => `${Math.floor(m/60)}:${String(m%60).padStart(2,"0")}`;
    return `<div class="conf-card"><h3>${a.dzien}: nakładanie ${f(o0)}–${f(o1)}</h3>` +
      `<p><b>${esc(a.kier)}</b> ${esc(a.przedmiot)} (${a.forma}) ${a.od}–${a.do}, s. ${esc(a.sala)}${esc(flagTxt(a))}</p>` +
      `<p><b>${esc(b.kier)}</b> ${esc(b.przedmiot)} (${b.forma}) ${b.od}–${b.do}, s. ${esc(b.sala)}${esc(flagTxt(b))}</p></div>`;
  }).join("") : "<p>Brak konfliktów 🎉</p>";
  document.getElementById("noteRoot").innerHTML = NIEPEWNOSCI
    .map(([k, t]) => `<div class="note-card"><b>${k}:</b> ${t}</div>`).join("");
})();

document.getElementById("printBtn").addEventListener("click", () => window.print());

// ===================== KONTAKTY / SPRAWY =====================
(function renderKont() {
  const nazwaStatusu = {
    ustalone: "ustalone", czekam: "czekam na plan",
    do_zmiany: "do zmiany", brak_planu: "brak planu",
  };
  const poz = k => {
    const c = k.kontakt;
    if (!c || !c.osoba) return '<p class="kontakt"><span class="brak">brak osoby kontaktowej — uzupełnij kierunki.yaml → kontakt</span></p>';
    const cz = [`<span class="osoba">${esc(c.osoba)}</span>`];
    if (c.rola)  cz.push(`<span>${esc(c.rola)}</span>`);
    if (c.pokoj) cz.push(`<span>pok. ${esc(c.pokoj)}</span>`);
    if (c.tel)   cz.push(`<span>tel. ${esc(c.tel)}</span>`);
    if (c.email) cz.push(`<a href="mailto:${esc(c.email)}">${esc(c.email)}</a>`);
    return `<p class="kontakt">${cz.join("")}</p>`;
  };
  document.getElementById("kontRoot").innerHTML = KIERUNKI.map(k => {
    const st = k.status || "czekam";
    return `<div class="kier-card st-${st}"><header>` +
      `<h3>${esc(k.kod)} <span class="nazwa">${esc(k.nazwa || "")}</span></h3>` +
      `<span class="st-badge st-${st}">${nazwaStatusu[st] || st}</span></header>` +
      (k.status_opis ? `<p class="opis">${esc(k.status_opis)}</p>` : "") +
      poz(k) +
      (k.sprawy && k.sprawy.length
        ? `<ul class="sprawy">${k.sprawy.map(s => `<li>${esc(s)}</li>`).join("")}</ul>`
        : "") +
      "</div>";
  }).join("");

  document.getElementById("notatkiRoot").innerHTML = NOTATKI.length
    ? `<ul class="sprawy">${NOTATKI.map(n => `<li>${esc(n)}</li>`).join("")}</ul>`
    : "<p>Brak notatek.</p>";

  const n = KIERUNKI.reduce((s, k) => s + (k.sprawy ? k.sprawy.length : 0), 0);
  document.getElementById("sprawyN").textContent = n ? `(${n})` : "";
})();

// ===================== ZAKŁADKI =====================
document.querySelector("nav.tabs").addEventListener("click", e => {
  const btn = e.target.closest("button[data-view]");
  if (!btn) return;
  for (const b of document.querySelectorAll("nav.tabs button"))
    b.setAttribute("aria-selected", b === btn ? "true" : "false");
  for (const s of document.querySelectorAll("main > section"))
    s.hidden = s.id !== "v-" + btn.dataset.view;
});
