#!/usr/bin/env python3
"""Buduje interaktywny plan zajęć (HTML) z plików danych.

Użycie: zbuduj_plan.py <ROK>        # np. 2026Z
        zbuduj_plan.py --nowy <ROK> # tworzy szkielety plików danych na nowy rok

Wejście (wszystko względem katalogu projektu):
  kierunki.yaml            — baza kierunków: nazwa, wydział, plany_url, kontakt (stała z roku na rok)
  stan/<ROK>.yaml          — status planu, sprawy do załatwienia, niepewności, notatki
  dane/<ROK>-zajecia.yaml  — zajęcia (dzień, godziny, sala, grupy, flagi) + zakres osi czasu
  szablon/plan.css.html    — styl (wspólny dla wszystkich lat)
  szablon/plan.js          — logika widoków (wspólna dla wszystkich lat)

Wyjście:
  wynik/<ROK>-plan.html    — jeden samodzielny plik, do otwarcia w przeglądarce
  wynik/<ROK>-plan.csv     — te same zajęcia w formie tabeli

Plik HTML jest artefaktem generowanym — nie edytuj go ręcznie, zmieniaj dane
albo szablon i uruchom skrypt ponownie.
"""
import csv
import json
import re
import sys
from pathlib import Path

import yaml

KAT = Path(__file__).resolve().parent.parent
SEMESTR_NAZWA = {"Z": "zimowy", "L": "letni"}


def wczytaj(sciezka):
    with open(sciezka, encoding="utf-8") as f:
        return yaml.safe_load(f)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def scal_kierunki(baza, stan):
    """Łączy stałą bazę kierunków ze stanem rocznym — tylko kierunki obecne w stanie."""
    out = []
    for kod, s in (stan.get("kierunki") or {}).items():
        b = (baza.get("kierunki") or {}).get(kod) or {}
        if not b:
            print(f"  uwaga: kierunek {kod} jest w stan/, ale nie w kierunki.yaml", file=sys.stderr)
        out.append(
            {
                "kod": kod,
                "nazwa": b.get("nazwa"),
                "wydzial": b.get("wydzial"),
                "plany_url": b.get("plany_url"),
                "kontakt": b.get("kontakt"),
                "status": (s or {}).get("status", "czekam"),
                "status_opis": (s or {}).get("status_opis"),
                "sprawy": (s or {}).get("sprawy") or [],
            }
        )
    return out


def skrot_wydzialu(nazwa):
    """'Wydział Inżynierii Kształtowania Środowiska i Geodezji' -> 'WIKŚiG'."""
    if not nazwa:
        return ""
    pomin = {"i", "w", "z", "oraz", "wydział"}
    skrot = "".join(
        w[0].upper() if w.lower() not in pomin else w[0].lower()
        for w in re.findall(r"[\wŁŚŻŹĆĄĘÓŃłśżźćąęóń]+", nazwa)
    )
    return skrot


def zbuduj_naglowek(stan):
    sem = SEMESTR_NAZWA.get(stan.get("semestr", "Z"), stan.get("semestr", ""))
    return f"Plan zajęć — semestr {sem} {stan['rok']}"


def zbuduj_html(rok, stan, kierunki, zajecia_plik):
    css = (KAT / "szablon/plan.css.html").read_text(encoding="utf-8")
    js = (KAT / "szablon/plan.js").read_text(encoding="utf-8")
    tytul = zbuduj_naglowek(stan)
    kody = " · ".join(k["kod"] for k in kierunki)
    opis = " ".join((stan.get("stan_zrodel_opis") or "").split())

    flagi = "".join(f'      <span class="flag">{esc(f)}</span>\n' for f in stan.get("flagi_globalne") or [])
    zrodla = ""
    for k in kierunki:
        if not k["plany_url"]:
            continue
        zrodla += (
            f'      <a href="{esc(k["plany_url"])}" target="_blank" rel="noopener">'
            f'<b>{esc(k["kod"])}</b> {esc(k["nazwa"] or "")} '
            f'<span class="wyd">{esc(skrot_wydzialu(k["wydzial"]))} ↗</span></a>\n'
        )

    dane_js = (
        "// ===================== DANE (generowane z plików YAML — nie edytuj tu) ====\n"
        f"const ZAJECIA = {json.dumps(zajecia_plik['zajecia'], ensure_ascii=False, indent=2)};\n\n"
        f"const OS_CZASU = {json.dumps(zajecia_plik.get('os_czasu') or {'od': '08:00', 'do': '16:00'}, ensure_ascii=False)};\n\n"
        f"const NIEPEWNOSCI = {json.dumps(stan.get('niepewnosci') or [], ensure_ascii=False, indent=2)};\n\n"
        f"const KIERUNKI = {json.dumps(kierunki, ensure_ascii=False, indent=2)};\n\n"
        f"const NOTATKI = {json.dumps(stan.get('notatki') or [], ensure_ascii=False, indent=2)};\n"
    )

    return f"""<!doctype html>
<html lang="pl">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(tytul)}</title>
{css}
<main>
  <header>
    <h1>{esc(tytul)}</h1>
    <div class="sub">{esc(stan.get("prowadzacy", ""))} · {esc(kody)} · stan źródeł: {esc(stan.get("stan_zrodel", ""))}{(" — " + esc(opis)) if opis else ""}</div>
    <div class="flags">
{flagi}    </div>
  </header>

  <nav class="tabs" role="tablist">
    <button role="tab" aria-selected="true" data-view="cal">Kalendarz</button>
    <button role="tab" aria-selected="false" data-view="list">Lista</button>
    <button role="tab" aria-selected="false" data-view="tbl">Tabela</button>
    <button role="tab" aria-selected="false" data-view="conf">Konflikty <span class="conf-count" id="confN"></span></button>
    <button role="tab" aria-selected="false" data-view="kont">Kontakty / sprawy <span class="conf-count" id="sprawyN"></span></button>
    <button type="button" class="print-btn" id="printBtn" title="Drukuj kalendarz na jednej stronie A4 (poziomo)">🖨 Drukuj A4</button>
  </nav>

  <div class="legend">
    <span><span class="sw w"></span>wykład</span>
    <span><span class="sw c"></span>ćwiczenia</span>
    <span><span class="sw kons"></span>konsultacje</span>
    <span><span class="sw k"></span>konflikt</span>
    <span class="chip">godziny wg planów źródłowych</span>
  </div>

  <section id="v-cal"><div class="cal-scroll"><div class="cal" id="calRoot"></div></div></section>
  <section id="v-list" hidden><div class="day-list" id="listRoot"></div></section>
  <section id="v-tbl" hidden><div class="tbl-scroll" id="tblRoot"></div></section>
  <section id="v-conf" hidden>
    <div id="confRoot"></div>
    <h2 class="sect">Niepewności / do wyjaśnienia</h2>
    <div id="noteRoot"></div>
  </section>
  <section id="v-kont" hidden>
    <div id="kontRoot"></div>
    <h2 class="sect">Notatki ogólne</h2>
    <div id="notatkiRoot"></div>
  </section>

  <footer class="sources">
    <h2>Źródła planów — sprawdź, czy są nowe wersje</h2>
    <p class="hint">Strony UPWr blokują automatyczne pobieranie (Anubis) — klikaj i sprawdzaj ręcznie w przeglądarce. Stan pobranych PDF-ów: {esc(stan.get("stan_zrodel", ""))}.</p>
    <div class="src-links">
{zrodla}    </div>
  </footer>
</main>

<script>
{dane_js}
{js}</script>
</html>
"""


def zapisz_csv(sciezka, zajecia):
    kol = ["dzien", "od", "do", "kier", "przedmiot", "forma", "sala", "grupy", "flagi", "zrodlo"]
    with open(sciezka, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(kol)
        for z in zajecia:
            w.writerow([" · ".join(z.get(k) or []) if k == "flagi" else (z.get(k) or "") for k in kol])


SZKIELET_ZAJECIA = """# Zajęcia w semestrze {sem} {rok_op} — jedyne źródło prawdy dla widoków.
# forma: W = wykład, C = ćwiczenia, K = konsultacje

os_czasu: {{ od: "08:00", do: "16:00" }}

zajecia: []
  # - {{ dzien: poniedziałek, od: "08:15", do: "10:00", kier: GP, przedmiot: "Statystyka",
  #     forma: C, sala: "2.04 H", grupy: "gr 1", flagi: ["projekt"] }}
"""

SZKIELET_STAN = """# Stan planu — semestr {sem} {rok_op}.
# Dane trwałe (nazwy, URL-e, osoby kontaktowe) → kierunki.yaml.

rok: "{rok_op}"
semestr: {semestr}
prowadzacy: "Maciej Karczewski"
stan_zrodel: ""            # data ostatniego pobrania PDF-ów
stan_zrodel_opis: ""
flagi_globalne: []

# status: czekam | ustalone | do_zmiany | brak_planu
# Wpisz tu kierunki z przydzialy/<rok>.tsv na ten semestr.
kierunki: {{}}
  # GP:
  #   status: czekam
  #   status_opis: ""
  #   sprawy:
  #     - "Napisać ws. ..."

niepewnosci: []
notatki: []
"""


def nowy_rok(rok):
    """Tworzy szkielety plików danych na nowy rok (nie nadpisuje istniejących)."""
    semestr = rok[-1].upper()
    r = int(rok[:4])
    rok_op = f"{r}/{str(r + 1)[-2:]}"
    sem = SEMESTR_NAZWA.get(semestr, semestr)
    (KAT / "dane").mkdir(exist_ok=True)
    (KAT / "stan").mkdir(exist_ok=True)
    (KAT / "pdf" / rok).mkdir(parents=True, exist_ok=True)
    for sciezka, tresc in [
        (KAT / f"dane/{rok}-zajecia.yaml", SZKIELET_ZAJECIA.format(sem=sem, rok_op=rok_op)),
        (KAT / f"stan/{rok}.yaml", SZKIELET_STAN.format(sem=sem, rok_op=rok_op, semestr=semestr)),
    ]:
        if sciezka.exists():
            print(f"  pomijam (już istnieje): {sciezka.relative_to(KAT)}")
        else:
            sciezka.write_text(tresc, encoding="utf-8")
            print(f"  utworzono: {sciezka.relative_to(KAT)}")
    print(f"  katalog na PDF-y: pdf/{rok}/")
    print(f"\nDalej: wrzuć PDF-y do pdf/{rok}/, wypełnij oba pliki YAML,")
    print(f"potem: python3 skrypty/zbuduj_plan.py {rok}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--nowy":
        if len(sys.argv) < 3:
            sys.exit("Podaj rok, np. --nowy 2027Z")
        return nowy_rok(sys.argv[2])

    rok = sys.argv[1]
    stan_p = KAT / f"stan/{rok}.yaml"
    zaj_p = KAT / f"dane/{rok}-zajecia.yaml"
    for p in (stan_p, zaj_p):
        if not p.exists():
            sys.exit(f"Brak pliku: {p.relative_to(KAT)}\nUruchom: zbuduj_plan.py --nowy {rok}")

    baza = wczytaj(KAT / "kierunki.yaml")
    stan = wczytaj(stan_p)
    zajecia_plik = wczytaj(zaj_p)
    zajecia_plik["zajecia"] = zajecia_plik.get("zajecia") or []
    for z in zajecia_plik["zajecia"]:
        z.setdefault("flagi", [])
        z.setdefault("przedmiot", "")
        z.setdefault("grupy", "-")
        z.setdefault("zrodlo", "")

    kierunki = scal_kierunki(baza, stan)
    html = zbuduj_html(rok, stan, kierunki, zajecia_plik)

    (KAT / "wynik").mkdir(exist_ok=True)
    out_html = KAT / f"wynik/{rok}-plan.html"
    out_html.write_text(html, encoding="utf-8")
    out_csv = KAT / f"wynik/{rok}-plan.csv"
    zapisz_csv(out_csv, zajecia_plik["zajecia"])

    n_sprawy = sum(len(k["sprawy"]) for k in kierunki)
    print(f"{out_html.relative_to(KAT)}  ({len(zajecia_plik['zajecia'])} zajęć, "
          f"{len(kierunki)} kierunków, {n_sprawy} spraw do załatwienia)")
    print(f"{out_csv.relative_to(KAT)}")


if __name__ == "__main__":
    main()
