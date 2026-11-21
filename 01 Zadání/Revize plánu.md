# Revize plánu (21. 11. 2026)

> **Aktualizace po rozhodnutích (21. 11. 2026, 9:07):** běžné ceny pro každý obchod chceme → u letákových obchodů se odvodí z „ceny před slevou“ (+ ruční zadání). Makro vyřazeno. Orchestrace ručně na PC (`aktualizuj.bat`) → body o GitHub Actions cronu a self-hosted runneru níže jsou **překonané** ([[02 Architektura/ADR/ADR-005 Ruční aktualizace na PC]]). Věrnostní ceny se zobrazují barevně s ⓘ. Jen lihoviny. Detail v [[09 Otevřené otázky]].


## Verdikt
**Architektonicky je plán reálný a zdarma proveditelný. Datově ne v původní podobě.** Původní předpoklad „scrapnu běžné ceny ze 7 supermarketů“ narazí na to, že většina řetězců už nemá online katalog s cenami. Realisticky dostupné jsou **akční ceny z letáků** u všech hlavních řetězců a **plný katalog** jen u některých. Doporučuji appku postavit kolem toho (název „Akce na pátek“ tomu ostatně sedí).

Podrobnost plánu: jako zadání produktu dobrý, jako vývojový plán nedostatečný — chyběly body níže. Ty jsou teď rozpracované ve vaultu.

## 1. Dostupnost dat — hlavní riziko 🔴
Stav k 11/2026 (ověřit ve spike, viz [[04 Zdroje/Přehled zdrojů]]):

| Řetězec | Plný katalog s cenami online? | Akce/leták online? | Poznámka |
|---|---|---|---|
| Tesco | ✅ nakup.itesco.cz | ✅ | e-shop běží; anti-bot ochrana |
| Billa | ⚠️ e-shop zrušen 31. 1. 2026, produktové stránky s cenami na billa.cz zřejmě zůstaly | ✅ | ověřit |
| Albert | ❌ e-shop zavřen 23. 12. 2025 | ✅ | ceny často jen s appkou Můj Albert |
| Lidl | ❌ (lidl-shop.cz je hlavně nepotravinový) | ✅ | |
| Kaufland | ❌ kaufland.cz je nepotravinový marketplace | ✅ sekce „Nabídka prodejny“ | Cloudflare + DataDome |
| Penny | ❌ | ✅ | |
| Makro | ⚠️ ceny jen po přihlášení s firemní registrací (IČO), B2B | ⚠️ | doporučuji vyřadit z MVP |

**Důsledek:** u Lidlu, Penny, Kauflandu a Albertu budeš znát cenu produktu jen tehdy, když je v akci. Detail produktu tak bude typicky ukazovat 2–4 obchody, ne 7. To je pro use-case „kde je to dnes nejlevnější“ v pořádku — nejnižší cena alkoholu bývá skoro vždy akční.

Další jemnosti, které plán neřešil:
- **E-shopová cena ≠ cena v prodejně** (Tesco online) a letákové slevy se na e-shop často nevztahují.
- **Věrnostní ceny** (Clubcard, Můj Albert, Billa Klub, Lidl Plus, Kaufland Card) — musí být v datech jako příznak, jinak budeš chodit pro cenu, kterou bez appky nedostaneš.
- **Platnost akcí** (typicky st–út, Lidl po–ne) — „dnes nejlevnější“ = filtr podle `valid_from/valid_to`.

## 2. Párování produktů napříč obchody 🔴
V plánu chybělo úplně a je to nejpracnější část. „Finlandia Vodka 40% 0,7l“ (Tesco) vs. „Finlandia vodka 0,7 l“ (leták Lidl) musí skončit jako jeden produkt; 0,5 l a 1 l jako různé. EAN obvykle u letáků není. Řešení: normalizace (značka, objem, % alk.) + fuzzy matching + ruční potvrzení nejistých párů. Viz [[03 Data/Párování produktů]].

## 3. Orchestrace 🟠
- **Vercel Cron na Hobby nestačí**: max 1× denně, spuštění kdykoliv v rámci zvolené hodiny, funkce max 300 s. Scraping 6 obchodů s Playwrightem se do serverless funkce nevejde.
- **Řešení:** GitHub Actions (cron) — zdarma, minuty neomezené pro veřejné repo, 2 000 min/měsíc pro soukromé. Viz [[02 Architektura/ADR/ADR-002 Orchestrace]].
- **Riziko:** Tesco a Kaufland mají anti-bot ochranu a IP adresy datacenter (GitHub runner) bývají blokované. Placené „unblockery“ nepřipadají v úvahu. **Záložní plán:** self-hosted GitHub runner na tvém PC (rezidenční IP, zdarma, ale PC musí být ráno zapnuté), případně Plánovač úloh ve Windows.

## 4. Databáze 🟢
Zdarma bez problému. Pozor: **Supabase Free projekt se po týdnu nečinnosti pozastaví**; Neon Free „usíná“ automaticky a probudí se sám. Doporučení: Neon Postgres. Viz [[02 Architektura/ADR/ADR-001 Databáze]]. Objem dat je malý (odhad desítky MB/rok i s historií).

## 5. Obrázky 🟢
Neukládat, odkazovat na CDN obchodů (hotlink) + fallback placeholder. Pro letákové položky jsou fotky horší kvality — při párování preferovat fotku z katalogového zdroje. Viz [[02 Architektura/ADR/ADR-004 Obrázky produktů]].

## 6. Právní stránka 🟠
Podmínky užití webů typicky automatizovaný sběr zakazují; v EU navíc existuje zvláštní právo pořizovatele databáze. Osobní, nekomerční použití s šetrným crawlem je nízké riziko, ale veřejně dostupná appka je technicky „zveřejnění“. Doporučení: `noindex`, nepropagovat, nekomerčně, šetrné rate limity. (Nejsem právník.) Viz [[07 Provoz/Právní a etické zásady]].

## 7. Co dalšího v plánu chybělo (doplněno)
- Definice „ceny“ (běžná / akční / věrnostní) a jejich priorita → [[03 Data/Datový model]]
- Cena za litr (srovnání 0,5 / 0,7 / 1 l)
- Co je „produkt“ (varianta = značka + název + objem)
- Zastaralá data a výpadky zdrojů → [[07 Provoz/Monitoring]]
- Spike na ověření zdrojů **před** psaním appky → [[08 Roadmapa/Roadmapa]] M0
- Testovatelnost scraperů (uložené HTML/JSON fixtures)

## Doporučené pořadí
1. **M0 Spike (1–2 večery):** u každého zdroje ověřit, co jde reálně stáhnout a odkud (GitHub runner vs. domácí PC). Výsledek zapsat do `04 Zdroje/*.md`. **Teprve pak** finálně zúžit rozsah.
2. MVP se 2–3 zdroji end-to-end (doporučuji Tesco + Lidl + Penny), pak přidávat další.
