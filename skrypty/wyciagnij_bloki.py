#!/usr/bin/env python3
"""Wyciąga bloki zajęć z siatkowego PDF-a planu (format UPWr).

Użycie: wyciagnij_bloki.py <plik.pdf> <nr_strony> [filtr_tekstu ...]

Mapuje współrzędne x prostokątów na oś czasu (nagłówki 7:30, 8:00, ...)
i wypisuje wszystkie bloki (lub tylko pasujące do filtra) z przedziałem
czasowym, wierszami grup i tekstem.
"""
import re
import sys

import pdfplumber


def cluster_words_into_boxes(page):
    """Grupuje prostokąty (rects/edges) strony w bloki zajęć na bazie ramek."""
    # Bloki zajęć to prostokąty z obramowaniem; pdfplumber widzi je jako rects.
    boxes = []
    for r in page.rects:
        w = r["x1"] - r["x0"]
        h = r["bottom"] - r["top"]
        if w < 15 or h < 8:  # odfiltruj kratkę siatki
            continue
        boxes.append(r)
    return boxes


def time_axis(page):
    """Zwraca listę (x, minuty_od_polnocy) na bazie etykiet godzin w nagłówku."""
    pts = []
    for w in page.extract_words():
        m = re.fullmatch(r"(\d{1,2})(00|30)", w["text"])
        if m and float(w["top"]) < page.height * 0.15:
            h, mm = int(m.group(1)), int(m.group(2))
            if 6 <= h <= 21:
                pts.append((w["x0"], h * 60 + mm))
    pts.sort()
    # deduplikacja (czasem etykieta występuje też na dole strony)
    dedup = []
    for x, t in pts:
        if not dedup or t > dedup[-1][1]:
            dedup.append((x, t))
    return dedup


def x_to_time(x, axis):
    """Interpolacja liniowa x -> minuty."""
    if not axis:
        return None
    for (x0, t0), (x1, t1) in zip(axis, axis[1:]):
        if x0 <= x <= x1:
            return t0 + (x - x0) / (x1 - x0) * (t1 - t0)
    # ekstrapolacja na końcach
    (x0, t0), (x1, t1) = (axis[0], axis[1]) if x < axis[0][0] else (axis[-2], axis[-1])
    return t0 + (x - x0) / (x1 - x0) * (t1 - t0)


def fmt(minutes):
    minutes = 15 * round(minutes / 15)  # siatka planu ma podziałkę 15 min
    return f"{int(minutes // 60):02d}:{int(minutes % 60):02d}"


DAY_NAMES = ["PONIEDZIAŁEK", "WTOREK", "ŚRODA", "CZWARTEK", "PIĄTEK", "SOBOTA", "NIEDZIELA"]


def day_bands(page):
    """Znajduje pionowe pasma dni po etykietach dni tygodnia (tekst obrócony,
    pisany od dołu do góry w lewym marginesie)."""
    rotated = [
        c
        for c in page.chars
        if c["x1"] < page.width * 0.075 and abs(c.get("matrix", (1, 0, 0, 1, 0, 0))[1]) > 0.5
    ]
    rotated.sort(key=lambda c: c["top"])
    # klastrowanie po pionowych przerwach
    clusters = []
    for c in rotated:
        if clusters and c["top"] - clusters[-1][-1]["top"] < 20:
            clusters[-1].append(c)
        else:
            clusters.append([c])
    bands = []
    for chars in clusters:
        word = "".join(ch["text"] for ch in sorted(chars, key=lambda ch: -ch["top"]))
        for d in DAY_NAMES:
            if d in word.upper().replace(" ", ""):
                bands.append((d, min(c["top"] for c in chars), max(c["bottom"] for c in chars)))
    bands.sort(key=lambda b: b[1])
    return bands


def box_day(box, bands):
    cy = (box["top"] + box["bottom"]) / 2
    best, bestd = None, 1e9
    for d, t, b in bands:
        c = (t + b) / 2
        if abs(c - cy) < bestd:
            best, bestd = d, abs(c - cy)
    return best


def words_in_box(page, box):
    out = []
    for w in page.extract_words():
        cx = (w["x0"] + w["x1"]) / 2
        cy = (w["top"] + w["bottom"]) / 2
        if box["x0"] - 1 <= cx <= box["x1"] + 1 and box["top"] - 1 <= cy <= box["bottom"] + 1:
            out.append(w["text"])
    return " ".join(out)


def group_rows(page, bands):
    """Wiersze grup: cyfry 1-8 w lewej kolumnie (x < ~8% szerokości)."""
    rows = []
    for w in page.extract_words():
        if re.fullmatch(r"[1-8]", w["text"]) and w["x0"] < page.width * 0.085:
            rows.append((w["text"], w["top"], w["bottom"]))
    return sorted(rows, key=lambda r: r[1])


def box_groups(box, rows, bands):
    day = None
    cy_top, cy_bot = box["top"], box["bottom"]
    hit = [g for g, t, b in rows if cy_top - 2 <= (t + b) / 2 <= cy_bot + 2]
    return hit


def classify_forma(box):
    """Zielone wypełnienie = wykład (W), inne (niebieskawe/szare) = ćwiczenia (C)."""
    c = box.get("non_stroking_color")
    if c is None:
        return "?"
    if isinstance(c, (int, float)):
        c = (c, c, c)
    if len(c) == 3:
        r, g, b = c
        if g > 0.6 and g > r + 0.05 and g > b + 0.05:
            return "W"
        return "C"
    return f"?{c}"


def main():
    pdf_path, page_no = sys.argv[1], int(sys.argv[2])
    filters = [f.lower() for f in sys.argv[3:]]
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_no - 1]
        axis = time_axis(page)
        bands = day_bands(page)
        rows = group_rows(page, bands)
        boxes = cluster_words_into_boxes(page)
        seen = set()
        for box in sorted(boxes, key=lambda b: (b["top"], b["x0"])):
            text = words_in_box(page, box)
            if not text.strip():
                continue
            if filters and not any(f in text.lower() for f in filters):
                continue
            t0 = x_to_time(box["x0"], axis)
            t1 = x_to_time(box["x1"], axis)
            day = box_day(box, bands)
            grp = box_groups(box, rows, bands)
            key = (day, round(t0), round(t1), text, tuple(grp))
            if key in seen:
                continue
            seen.add(key)
            forma = classify_forma(box)
            print(f"{day:<13} {fmt(t0)}-{fmt(t1)}  {forma}  grupy={','.join(grp) or '?'}  | {text}")


if __name__ == "__main__":
    main()
