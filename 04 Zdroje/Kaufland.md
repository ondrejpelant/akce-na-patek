# Kaufland
- **Web:** https://www.kaufland.cz — hlavní web je **nepotravinový marketplace**; potravinové akce v sekci **„Nabídka prodejny“**.
- **Typ dat:** jen akční nabídka (+ **Kaufland Card** ceny).
- ⚠️ Web je za **Cloudflare a DataDome** (dle komerčních scraperů). Obcházení ochran nebudeme dělat. Pokud nepůjde normální požadavek ani z domácí IP s Playwrightem při nízké frekvenci → **zdroj vyřadit**.
- Ceny se mohou lišit podle prodejny → zvolit jednu (domovskou) prodejnu.
- **Priorita:** P3

## Spike checklist
- [ ] Je „Nabídka prodejny“ dostupná bez CAPTCHA z domova? Z GH?
- [ ] Závislost na zvolené prodejně (cookie/parametr)
- [ ] Struktura dat, platnost
- [ ] robots.txt, podmínky, fixtures

## Rozhodnutí po spike
_(doplnit)_
