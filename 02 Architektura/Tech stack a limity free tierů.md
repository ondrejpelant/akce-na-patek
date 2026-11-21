# Tech stack a limity free tierů

> Limity ověřeny 21. 11. 2026. Free tiery se mění — při registraci zkontroluj a případně uprav tuto note.

## Vercel Hobby
- Zdarma, určeno pro osobní/nekomerční projekty.
- Funkce: max **300 s**.
- Cron: **max 1× denně**, spuštění kdykoliv v rámci zvolené hodiny → nepoužíváme, aktualizace se spouští ručně na PC.
- Pro nás stačí: SSR/ISR stránky, pár lehkých route handlerů.

## Neon Postgres Free (zvoleno)
- 1 GB úložiště na projekt, compute škáluje do nuly a sám se probouzí (cold start ~stovky ms).
- Limit compute hodin měsíčně — pro 1 uživatele + denní dávku bohatě stačí.
- Rozšíření: `pg_trgm`, `unaccent` (ověřit dostupnost v M1).

## Supabase Free (alternativa, nezvoleno)
- 500 MB DB, 1 GB storage, 2 projekty.
- **Projekt se po týdnu nečinnosti pozastaví** a musí se ručně obnovit — denní zápis z cronu by to měl držet aktivní, ale je to zbytečné riziko.

## GitHub Actions
- Jen **CI** (testy scraperu, build webu) při pushi. Scraping neběží v GitHubu — viz [[ADR/ADR-005 Ruční aktualizace na PC]].
- Soukromé repo: 2 000 min/měsíc, CI spotřebuje jednotky minut.

## Odhad objemu dat
- ~6 obchodů × ~300–1 500 alkoholových položek ≈ 5–8 tis. `store_product`.
- SCD2 ceny: řádek jen při změně. Letáky se mění týdně → ~2–4 tis. nových řádků týdně ≈ 150 tis./rok ≈ desítky MB. Daleko pod limitem.
