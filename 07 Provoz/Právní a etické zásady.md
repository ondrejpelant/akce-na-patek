# Právní a etické zásady

> Nejsem právník; toto je pragmatický rámec pro osobní projekt, ne právní rada.

## Rizika
- **Podmínky užití** webů řetězců typicky zakazují automatizovaný sběr dat.
- **Zvláštní právo pořizovatele databáze** (autorský zákon č. 121/2000 Sb., § 88 a násl.; EU směrnice 96/9/ES) — opakované vytěžování podstatné části databáze může být neoprávněné.
- **Obrázky** jsou chráněné autorským právem → jen odkazujeme (hotlink), nekopírujeme.
- **Obcházení technických ochran** (CAPTCHA, anti-bot, login) je samostatné a vyšší riziko.

## Zásady projektu (závazné i pro Claude Code)
1. Osobní, **nekomerční** použití. Žádné reklamy, affiliate, prodej dat.
2. Web není indexovaný (`noindex`, `robots.txt` Disallow) a nepropaguje se.
3. Respektujeme `robots.txt`.
4. **Neobcházíme** CAPTCHA, anti-bot ochrany ani přihlášení. Když zdroj blokuje, vyřadí se nebo se přejde na nižší frekvenci z domácí IP bez maskování.
5. Šetrnost: 1× denně, ≤ 1 požadavek / 2 s, jen kategorie alkoholu, identifikovatelný User-Agent.
6. Stahujeme jen fakta potřebná pro srovnání (název, objem, cena, platnost, URL, URL obrázku).
7. Pokud nás řetězec požádá o ukončení → okamžitě ukončit.
