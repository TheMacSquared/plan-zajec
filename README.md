# Plan zajęć — automatyzacja

Cel: z przydziałów dydaktycznych + planów zajęć poszczególnych kierunków budować
zbiorczy plan zajęć (arkusz, lista, .ics) i wykrywać konflikty.

## Struktura

- `przydzialy/RRRR-RRRR.tsv` — przydziały dydaktyczne na dany rok akademicki
  (wklejane raz na początku roku; kolumny jak w systemie uczelnianym).
- `kierunki.yaml` — stała baza kierunków: kod → nazwa, wydział, URL strony z rozkładami.
- `pdf/2025Z/` — skrzynka wrzutowa: pobrane pliki planów na semestr zimowy 2025/26.
  Nazwa pliku: `<KOD_KIERUNKU>.pdf` (np. `GP.pdf`, `OZE.pdf`); jeśli plan jest
  w kilku plikach, `GP-1.pdf`, `GP-2.pdf`.
- `wynik/` — wygenerowane widoki: zbiorcza tabela, arkusz, lista, .ics, raport konfliktów.

## Przepływ (semestr zimowy 2025/26)

1. Pozyskanie PDF-ów z planami (patrz kierunki.yaml → plany_url).
   Uwaga: strony UPWr są chronione przez Anubis (anty-bot) — pliki trzeba pobrać
   przez prawdziwą przeglądarkę (ręcznie albo przez Claude in Chrome).
2. Claude czyta PDF-y i wyciąga zajęcia pasujące do przydziału
   (kierunek + semestr studiów + przedmiot, W i C osobno).
3. Normalizacja do wspólnej tabeli: dzień/data, godziny, sala, grupa, przedmiot, forma, kierunek.
4. Generowanie widoków + raport konfliktów (nakładające się przedziały czasowe).

## Przydział na semestr zimowy 2025/26

| Kierunek | Przedmiot | Sem. studiów | Forma | Godziny |
|---|---|---|---|---|
| GP (I st., stacj.) | Statystyka | 3 | W 15h + C 30h (2 grupy) | |
| IDSaT (I st., stacj.) | Statystyka matematyczna | 1 | W 30h + C 30h (1 grupa) | |
| IBezp (I st., stacj.) | Analiza ryzyka | 7 | W 12h + C 24h (1 grupa) | |
| OZE (II st., stacj.) | Statystyczna analiza danych | 2 | W 15h + C 40h (2 grupy) | |
