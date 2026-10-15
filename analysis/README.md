# Shared quarterback EPA standard

All three quarterback articles use `nfelo-compatible-v1`, implemented in `qb_epa.py`.

Use raw nflfastR `epa`, not receiver-fumble-adjusted `qb_epa`. Attribute a play by nflfastR `id`, limited to quarterback IDs. Include `pass == 1` or a non-aborted `rush_attempt == 1`, with a recorded down and nonmissing EPA. Exclude kneels, spikes and two-point attempts. Include sacks, scrambles, designed QB runs and eligible penalty plays. Aborted passing plays are not blanket-excluded. No win-probability, quarter or turnover filter applies.

Total EPA is the sum of these plays. EPA/play is total EPA divided by their count. Success rate is the fraction with raw EPA greater than zero. Never combine one definition's numerator with another definition's denominator.

Regular season is the default; postseason must be selected explicitly and kept separate. Single-season rate and historical leaderboard qualification is 300 plays. Multi-year Allen–Jackson minimums remain 1,600 (2018–25), 400 (2018–19), 1,200 (2020–25) and 600 (2023–25). Postseason window minimums are documented in the article's embedded data. All-time is shorthand for available play-by-play since 1999, not all NFL history. MVP appendix scope starts in 2000.

`qb_seasons.csv` freezes 1999–2025 season values used in the revision. `total_epa_rank` is the within-season total rank among all quarterback IDs; `rate_rank` and `sr_rank` are within-season ranks among QBs with 300 plays. Recompute historical ranks across the specified year window. Do not treat the table's annual ranks as historical ranks.

`epa_standard.json` records five independent nfelo game-log sum benchmarks, all reproduced within 0.001 EPA, and the chosen version. That verifies these examples, not every provider number or leaderboard rank. Providers can change data and qualifying thresholds. nfelo's label “EPA/dropback” should not be substituted for this article's broader QB EPA/play label.

Official traditional box-score totals are separately sourced. Do not derive them from the EPA-eligible play set. Total TD accounted for includes passing, rushing and receiving.

Team offense/defense uses raw EPA and the shared exclusions across all offensive player IDs; it is distinct from QB EPA. For the Maye pass/run split, dropbacks additionally require `qb_dropback == 1`, and designed rushes require `rush_attempt == 1` without the dropback flag. Penalties that cannot be assigned to a category are omitted from that split. Scrambles additionally require `qb_scramble == 1`; eligible associated penalties remain. Goal-line rushing additionally requires a rushing attempt from five yards or closer.

The 1999 and 2000 released play-by-play snapshots have missing games. No affected 1999/2000 season appears in the revised historical top 30 total-EPA list or MVP top-20 EPA/rate appendix. Historical playoff rankings use available PBP appearances.

Sources: [nflverse PBP](https://github.com/nflverse/nflverse-data/releases/tag/pbp), [nflfastR field dictionary](https://www.nflfastr.com/articles/field_descriptions.html), [nfelo benchmarks](https://www.nfeloapp.com/qb-rankings/).
