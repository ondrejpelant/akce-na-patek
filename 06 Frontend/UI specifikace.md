# UI specifikace

Mobile-first, světlý čistý design inspirovaný Vinted: velké fotky, minimum textu, cena výrazně.

## Úvodní stránka `/`
```
┌──────────────────────────────┐
│ 🍾 Akce na pátek             │  ← sticky header
│ [🔍 Hledat (finlandia…)    ] │
│ (Vše)(Rum)(Vodka)(Gin)(Whi…→ │  ← horizontálně scrollovatelné chipy
│ Řadit: Nejlevnější ▾  ☐ Jen akce │
├──────────────┬───────────────┤
│ ┌──────────┐ │ ┌──────────┐  │
│ │  FOTKA   │ │ │  FOTKA   │  │  ← čtverec, object-contain, bílé pozadí
│ │ [-35 %]  │ │ │          │  │  ← badge slevy, pokud regular_czk
│ └──────────┘ │ └──────────┘  │
│ 249,90 Kč    │ 389,00 Kč     │  ← tučně, největší text karty
│ Penny · do 25.11.│ Tesco ⓘ   │  ← obchod + platnost; věrnostní cena = jiná barva + ⓘ
│ Finlandia 0,7 l │ Jameson 1 l │  ← 1 řádek, ellipsis
│ 357 Kč/l · 3 obch.│ …        │  ← šedě, malé
└──────────────┴───────────────┘
```
- **Banner stáří dat** pod headerem: „Data z dnes 9:15“ (šedě) / „Data jsou 4 dny stará — spusť aktualizaci“ (oranžově, > 2 dny).
- Grid: 2 sloupce mobil, 3 tablet, 5–6 desktop.
- Stav filtrů v URL: `/?q=finlandia&cat=vodka&sort=price&promo=1` (sdílitelné, funguje zpět).
- Vyhledávání: debounce 300 ms, server-side, `similarity()`/`ILIKE` nad `search_text` (bez diakritiky).
- Stránkování: „Načíst další“ (48 položek), ne nekonečný scroll.
- Prázdný stav: „Nic nenalezeno. Zkus jiný název, nebo ten produkt není v žádné aktuální akci.“

## Detail `/p/[slug]`
```
← Zpět
[        VELKÁ FOTKA        ]
Finlandia Vodka
0,7 l · 40 %
Nejlevněji dnes: 249,90 Kč v Penny

┌───────────────────────────────┐
│ [logo] Penny      249,90 Kč   │ ← nejlevnější zvýrazněný
│ Akce do 25. 11. · 357 Kč/l    │
├───────────────────────────────┤
│ [logo] Tesco      279,90 Kč ⓘ │ ← fialová cena = věrnostní
│ Clubcard · do 30. 11.         │
├───────────────────────────────┤
│ [logo] Tesco      349,90 Kč   │
│ Běžná cena                    │
├───────────────────────────────┤
│ [logo] Lidl       329,90 Kč   │ ← běžná cena odvozená z letáku
│ Běžná cena · k 12. 9.         │
├───────────────────────────────┤
│ [logo] Albert  — cena neznámá │ ← šedě; produkt jsme tu viděli, ale cenu teď neznáme
└───────────────────────────────┘
Aktualizováno dnes 4:12 · ceny bez záruky
```
- Řádek = jedna dnes platná cena; obchod může mít víc řádků (např. Tesco Clubcard + běžná). Vše seřazeno vzestupně (od 21. 11. 2026; dřív jen nejnižší cena za obchod).
- Pod seznamem šedě „Bez ceny: …" — aktivní obchody, kde jsme produkt neviděli nebo jejich ceny nestahujeme.
- Cena ověřená před víc než 2 dny má v podtitulku „· ověřeno DD. M." (Tesco se obnovuje po výpisech).
- Sekce „Další {značka} v obchodech" — až 8 produktů stejné značky s dnešní cenou (miniatura, objem, obchody, nejnižší cena, Kč/l); napřed ty z obchodů, kde aktuální produkt chybí.
- Fotka nahoře velká (čtverec max. 320 px), pod ní název.
- Pokud je produkt v akci, pod akční cenou přeškrtnutě běžná cena (`regular_czk`) a % slevy.
- Každý řádek odkazuje do obchodu (`url`), `target=_blank rel=noopener`.
- Běžná cena z letáku/ruční starší než 60 dní → štítek „může být neaktuální“.
- Fáze 2: mini graf historie ceny (SVG sparkline, žádná knihovna).

## Věrnostní ceny (rozhodnuto 21. 11. 2026)
- Počítají se do nejnižší ceny, ale cena je **barevně odlišená** (např. fialová `text-violet-600`, ne červená — ta je pro slevy) a vedle je ikona **ⓘ**.
- Na ⓘ vysvětlivka: „Cena platí jen s věrnostní kartou Clubcard.“ / „…jen s aplikací Můj Albert.“ (název z `store.loyalty_name`).
- ⚠️ Na telefonu **hover neexistuje** → ⓘ je tlačítko: na desktopu tooltip při najetí, na mobilu popover po **ťuknutí** (zavře se ťuknutím mimo). Implementace: `<button aria-label=…>` + Popover (např. Radix UI / headless komponenta), ne jen `title` atribut.
- Na kartě v mřížce stejné pravidlo (barva + ⓘ), aby bylo hned vidět, že „nejnižší“ je s kartou.

## Ostatní
- `/status` — tabulka obchodů: poslední běh, status, počet položek. Bez odkazu z menu.
- `<meta name="robots" content="noindex, nofollow">` na všech stránkách + `robots.txt` Disallow: / .
- Patička: „Osobní nekomerční projekt. Ceny bez záruky, ověř v obchodě. Nadměrné pití škodí zdraví.“
- Dark mode: ne v MVP.
- PWA (ikonka na ploše telefonu): nice-to-have, manifest + ikona, bez service workeru.
