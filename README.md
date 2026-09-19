# Plan zajęć — automatyzacja

Cel: z przydziałów dydaktycznych + planów zajęć poszczególnych kierunków budować
zbiorczy plan zajęć (kalendarz, lista, tabela), trzymać w jednym miejscu sprawy
organizacyjne (do kogo pisać, co jeszcze niejasne) i wykrywać konflikty.

Wynik to jeden samodzielny plik HTML — otwierasz w przeglądarce, działa offline,
ma przycisk druku A4.

## Użycie

```bash
python3 skrypty/zbuduj_plan.py 2026Z          # przebuduj plan na dany semestr
python3 skrypty/zbuduj_plan.py --nowy 2027Z   # szkielety plików na nowy rok
```

Kod oznaczenia semestru: `RRRR` + `Z` (zimowy) albo `L` (letni), np. `2026Z`, `2026L`.

`wynik/*.html` jest **artefaktem generowanym** — nie edytuj go ręcznie.
Zmieniasz dane (YAML) albo szablon i uruchamiasz skrypt ponownie.

## Struktura

Dane trwałe (raz ustawione, rzadko ruszane):

- `kierunki.yaml` — baza kierunków: kod → nazwa, wydział, URL strony z rozkładami
  oraz `kontakt` — osoba odpowiedzialna za plan (pokój, telefon, email). To do niej
  piszesz w sprawie zmiany sali, godzin czy łączenia grup.
- `przydzialy/RRRR-RRRR.tsv` — przydziały dydaktyczne na rok akademicki
  (wklejane raz na początku roku; kolumny jak w systemie uczelnianym).
- `szablon/plan.css.html`, `szablon/plan.js` — styl i logika widoków, wspólne dla
  wszystkich lat. Poprawka tutaj działa na każdy rocznik po przebudowaniu.

Dane roczne (nowe na każdy semestr):

- `pdf/<ROK>/` — skrzynka wrzutowa: pobrane PDF-y z planami kierunków.
- `dane/<ROK>-zajecia.yaml` — zajęcia: dzień, godziny, sala, grupa, forma, flagi.
  Plus `os_czasu` — zakres godzin na osi kalendarza.
- `stan/<ROK>.yaml` — to, co się zmienia w trakcie ustalania planu: status per
  kierunek (`czekam` / `ustalone` / `do_zmiany` / `brak_planu`), sprawy do
  załatwienia, niepewności, notatki, data stanu źródeł.

Wyjście:

- `wynik/<ROK>-plan.html` — plan interaktywny (5 zakładek + druk A4).
- `wynik/<ROK>-plan.csv` — te same zajęcia jako tabela.

## Zakładki w wygenerowanym planie

| Zakładka | Co pokazuje | Skąd dane |
|---|---|---|
| Kalendarz | siatka tygodnia, bloki klikalne (rozwijają szczegóły) | `dane/` |
| Lista | zajęcia dzień po dniu | `dane/` |
| Tabela | wszystko w jednej tabeli | `dane/` |
| Konflikty | nakładające się bloki (liczone automatycznie) + niepewności | `dane/` + `stan/` |
| Kontakty / sprawy | status kierunku, do kogo pisać, lista spraw, notatki | `kierunki.yaml` + `stan/` |

## Przepływ na nowy semestr

1. `python3 skrypty/zbuduj_plan.py --nowy 2027Z` — tworzy `dane/2027Z-zajecia.yaml`,
   `stan/2027Z.yaml` i katalog `pdf/2027Z/`.
2. Wklej przydziały do `przydzialy/2027-2028.tsv`, wypisz w `stan/2027Z.yaml`
   kierunki z tego semestru (klucz `kierunki`).
3. Pozyskaj PDF-y z planami (linki: `kierunki.yaml` → `plany_url`) do `pdf/2027Z/`.
   Uwaga: strony UPWr są chronione przez Anubis (anty-bot) — pliki trzeba pobrać
   przez prawdziwą przeglądarkę (ręcznie albo przez Claude in Chrome).
4. Wyciągnij bloki z PDF-a i przepisz swoje zajęcia do `dane/2027Z-zajecia.yaml`:
   ```bash
   python3 skrypty/wyciagnij_bloki.py pdf/2027Z/plik.pdf 1 statystyka
   ```
5. Sprawdź, czy w `kierunki.yaml` są osoby kontaktowe dla nowych kierunków
   (`kontakt: null` = do uzupełnienia).
6. `python3 skrypty/zbuduj_plan.py 2027Z` i otwórz `wynik/2027Z-plan.html`.
7. W trakcie semestru: plan się zmienia → poprawiasz YAML, przebudowujesz.
   Sprawy załatwione usuwasz z `sprawy:`, status podnosisz na `ustalone`.

## Wymagania

Python 3 + `pyyaml` (generator), `pdfplumber` (odczyt PDF-ów).

## Historia

Wcześniej informacje organizacyjne (kontakty, statusy, sprawy) leżały w luźnym
pliku `plan-semestr-zimowy-2025-26.md` w katalogu głównym repozytorium — teraz
w `_archive/`, a treść rozłożona na `kierunki.yaml` i `stan/<ROK>.yaml`.
