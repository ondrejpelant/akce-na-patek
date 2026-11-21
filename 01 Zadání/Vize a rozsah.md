# Vize a rozsah

## Problém
Chci koupit konkrétní alkohol (např. Finlandia 0,7 l) a nevím, ve kterém supermarketu je dnes nejlevnější. Letáky jsou roztříštěné, ceny se mění týdně.

## Řešení
Webová appka, kde najdu produkt podle fotky/názvu a hned vidím nejnižší dnešní cenu + srovnání napříč obchody.

## Uživatel
Jen já (osobní použití). Žádné účty, žádné přihlášení, žádný košík, žádné notifikace (v MVP).

## Funkce — MVP (must have)
1. **Úvodní stránka** — mřížka karet (styl Vinted): fotka produktu, nejnižší cena, obchod, objem.
2. **Vyhledávání** — fulltext podle názvu/značky, tolerantní k diakritice („koňak“ = „konak“).
3. **Kategorie** — jen lihoviny: rum, vodka, gin, whisky, koňak/brandy, likér, tequila, pálenky, bylinné… viz [[03 Data/Kategorie]].
4. **Detail produktu** — kolik produkt stojí v jednotlivých obchodech, seřazeno od nejnižší. Každý obchod má výchozí běžnou cenu; když je produkt v akci, po dobu akce se zobrazí akční cena. Věrnostní ceny barevně odlišené s ikonou ⓘ a vysvětlivkou. Dále platnost akce, cena za litr, kdy naposledy ověřeno, odkaz do obchodu.
5. **Aktualizace jedním klikem** — ručně na mém PC před nákupem (`aktualizuj.bat`), viz [[05 Scraper/Aktualizace dat]].

## Should have (po MVP)
- Řazení: nejlevnější / největší sleva / cena za litr.
- Filtr „jen akce“.
- Graf historie ceny v detailu (data máme díky SCD2 zdarma).
- Stránka `/status` — kdy proběhl poslední úspěšný scrape každého obchodu.

## Won't have
- Přihlašování, uživatelské účty, oblíbené, hlídací psi, e-maily.
- Nákup / košík / affiliate.
- Komerční provoz (viz [[07 Provoz/Právní a etické zásady]]).

## Nefunkční požadavky
- **Náklady 0 Kč** (Vercel Hobby, free DB, scraping na vlastním PC).
- **Mobile-first** — používám v obchodě na telefonu. Načtení úvodní stránky < 2 s na 4G.
- **Čerstvost dat:** web vždy ukazuje, kdy proběhla poslední aktualizace (banner). Akce se zobrazují jen v době platnosti. Běžné ceny se nezahazují kvůli stáří, ale nad 60 dní se označí „může být neaktuální“.
- **Odolnost:** výpadek jednoho scraperu nesmí shodit ostatní ani web.
