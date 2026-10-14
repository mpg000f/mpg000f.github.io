# Josh Allen and the Arm Punt: reproduction notes

The article's primary comparison covers the **2022–2026 YTD regular seasons**, through
October 12, 2026. The 2026 season is partial and labeled throughout. `../data/results.json` contains the reviewed
headline counts, and `../data/allen-plays.json` contains Allen's qualifying play
descriptions, IDs, depths, EPA and FTN labels, including the 2026 example.

## Run

Install pandas, numpy, scipy and scikit-learn in your own Python environment, then:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python analysis/reproduce.py
```

The script downloads the public sources into an ignored `.cache/` directory,
fits the decision and net-distance models, joins FTN charting, filters registered
quarterbacks, and verifies the summary against the article snapshot. Downloads
include 2021 for training, 2022–2026 YTD for the main analysis. The script fixes the game-date cutoff at October 12, 2026. Source files and the player registry can be corrected after publication;
the final assertions intentionally flag changes rather than overwrite the snapshot.
Dependencies used for the published calculation include scikit-learn 1.8.0.

## Exact definition

- Third-down pass attempt, excluding sacks, scrambles, spikes, kneels, two-point
  attempts and nullified plays.
- At least 15 seconds remaining in the half before the snap.
- Predicted punt probability of at least 0.80 after a hypothetical incompletion.
- Air yards at least predicted net punt distance minus 10 yards.
- Risk outcome is an actual interception **or** an FTN interception-worthy flag.
  A pass satisfying both is counted once. Returns never affect classification.

The punt classifier is `HistGradientBoostingClassifier`, 160 iterations, 15
maximum leaf nodes, 60 minimum observations per leaf, L2 regularization 2,
learning rate 0.07 and random seed 8. Its pre-decision inputs are distance, field
position, quarter, half/game clocks, score differential, timeouts and home status.
The hypothetical incomplete pass consumes five seconds. Models for 2021–2025
exclude the season being scored; 2026 uses 2021–2025 training data. The training
target is observed punting, not a fourth-down optimality recommendation.

Net punt distance uses `HistGradientBoostingRegressor`, 100 iterations, 6 maximum
leaf nodes, 100 minimum observations per leaf and random seed 8. It models net
yards from field position on nonblocked, penalty-free 2021–2025 punts. Touchbacks
are evaluated at the receiving team's 20. This is a field-position adjustment,
not a punt-outcome simulation. Other QBs are pooled by attempts, excluding Allen.

## Rams counterfactual

The article separately uses nflfastR's expected-points model to compare the Rams
interception with a hypothetical incompletion and average punt. Buffalo's initial
state: third-and-6 at its own 16, 37 seconds left in the second quarter, away team,
dome, two timeouts for each team. Recorded pre-play EP: **0.0952200055**; actual
interception EPA: **−1.2084954881**.

Counterfactual: incompletion consumes five seconds; punt consumes seven more;
net punt distance **42.2422** yards; Rams then have first-and-10 near their own
41.76 with 25 seconds left and the same timeouts. The two-play Buffalo EPA is
approximately **−1.2911**. The interim fourth-down EP cancels when summing both
plays. This calculation is not included in the count-reproduction script.
Use the EP model from https://github.com/nflverse/fastrmodels with those inputs
to reproduce it. Reasonable changes to elapsed time or punt distance can reverse
the very small difference from the actual interception.

## Jacksonville counterfactual and video

The second example is the 2023 Week 5 interception against Jacksonville, game
`2023_05_JAX_BUF`, play 3466. Pre-snap: third-and-15, Buffalo's own 41, 13:16 left
in the fourth quarter, neutral site, outdoors, Buffalo two timeouts and
Jacksonville three. nflfastR pre-play EP is **−0.1687361938**. The actual pick
leaves Jacksonville at its own 7 with 13:06 remaining; EPA is **+0.1921405606**.

The same net-distance model used for qualification estimates **42.4124130** punt
yards from Buffalo's 41. After a five-second incompletion and seven-second punt,
Jacksonville would have first-and-10 at its own **16.5875870** with 13:04 remaining,
three timeouts versus Buffalo's two. Its model EP is negated to express the state
from Buffalo's perspective, then Buffalo's initial EP is subtracted. Combined
incompletion-plus-punt EPA is **−0.4622898845**. The interception is therefore
**0.6544304451 EPA** better than that assumed punt alternative. The interim
fourth-down EP cancels when the two hypothetical plays are summed. These results
are stored in `../data/jaguars-counterfactual.json`.

The Rams source marks its video non-embeddable. A visible poster/watch card
opens the original post. The Jaguars source permits embedding, and its original
720p hosted media URL is used in a native browser player. No video is rehosted.
Public oEmbed and syndication responses were used to verify the source posts:

- Rams: https://x.com/brgridiron/status/2109819918937911418
- Jaguars: https://x.com/Jaguars/status/1711050700904415500
- Official Jaguars fallback: https://www.jaguars.com/video/can-t-miss-play-darious-williams-intercepts-josh-allen-s-60-yard-pass

The football premise of the arm punt is the lack of a safer realistic first-down
conversion by the time of the decision. The statistical filters do **not** prove
that premise on a particular snap. Nor do they identify earlier missed reads.

## Sources, attribution and limitations

- Play-by-play: https://github.com/nflverse/nflverse-data/releases/tag/pbp
- FTN charting: https://nflreadr.nflverse.com/reference/load_ftn_charting.html
- FTN dictionary: https://nflreadr.nflverse.com/articles/dictionary_ftn_charting.html
- QB registry: https://github.com/nflverse/nflverse-data/releases/tag/players
- EP model: https://github.com/nflverse/fastrmodels

**FTN Data via nflverse** supplies the manual charting. The accompanying FTN-derived
JSON datasets are shared under **CC BY-SA 4.0**:
https://creativecommons.org/licenses/by-sa/4.0/. The flags reflect charting
judgment, not proof of a dropped interception or the quarterback's intent.

Thresholds were chosen during exploratory analysis of Allen's plays. Nine
qualifying Allen risk throws underpin the main result. Identical filters and
opportunity normalization do not establish intent, causality, optimality, or exact
balance in pressure, coverage, receivers and coaching behavior.


## Individual QB comparison and short passes
Run `python analysis/compare_qbs.py` after `reproduce.py`. The supporting `data/qb-comparison.json` preserves every QB, counts, rates, distance to gain, missingness, conversion outcomes and a throwaway-excluded sensitivity. Individual ranks require at least 100 qualifying opportunities; 39 QBs qualify in this snapshot. Period and eligibility are identical to the headline comparison. The notable-QB table is a named selection; the expandable tables provide all qualified players.

Short of the sticks is `air_yards < ydstogo`, with all known-depth attempts as denominator (including incompletions and recorded throwaways). All 10,905 qualifying attempts have known depth. Conversion is a recorded first down or touchdown, including gains after the catch. A charted checkdown is FTN `read_thrown == "CHK"` and uses all qualifying attempts as denominator. Designed reads, screens, scramble drills and blank reads are not recast as checkdowns. FTN’s dictionary notes that 2022 primary reads were uncoded; these blanks are not missing checkdown classifications by assumption. No claim that all short throws are checkdowns, or all checkdowns are bad decisions, follows from these definitions. Context distributions can differ even under identical inclusion rules.

Mahomes illustration: `2025_14_HOU_KC`, play `3299`: third-and-6 at KC’s own 42, 42 air yards, intercepted by Kamari Lassiter at Houston’s own 16 with no return. Incompletion punt probability 0.991424; expected net punt 42.158944 yards; threshold 32.158944. This play meets the same criteria. Video: https://x.com/MLFootball/status/1997876310484431179. Its source disables off-site embedding; the linked preview opens the original post.

Rams table explicitly distinguishes the observed post-interception field position (LA own 43) from the counterfactual punt estimate (LA own 41.757798, rounded 41.8). We have not modeled an average field position over possible interception returns.


## All qualifying interception outcomes

Install `xgboost`, then run `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python analysis/evaluate_outcomes.py` after `reproduce.py`. The audit file `../data/interception-outcomes.json` contains all 41 qualifying interceptions (six Allen, 35 other QBs), input states, net-punt estimates, pre-EP validation, actual post-state validation, hypothetical states, QB/season aggregates and scenario results. Both validations match recorded values within 1e-5 (actual errors in this snapshot are below 1.1e-14). Existing snapshots are source-backed, not simulated interception outcomes.

The EP model is pinned to fastrmodels commit `f7c9d05bec81cd310bd1b4cc951b8a451b6aba6c`, `data/ep_model.rda`. The script extracts its serialized UBJSON booster and records its SHA-256. Its feature order and seven score-class weights match nflfastR `R/helper_add_ep_wp.R`. Schedule roof and neutral-site metadata come from https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv; neutral-site home flags are zero for both possessions.

For a play with `yardline_100 = Y` and modeled net punt `N`, the opponent’s receiving yard line measured from its own goal is **Y − N**. The receiving team’s EP-model yardline_100 is **100 − (Y − N)**. Incompletion consumes five seconds, punt seven, and possession swaps both timeouts and the home flag. New down is first-and-10 (or goal-to-go if applicable). The two hypothetical plays telescope to `-receiving_EP - original_EP`; no intervening fourth-down EP remains in the sum. Delta is `actual_interception_EPA - hypothetical_two_play_EPA`, positive when the actual pick is more favorable for the throwing offense. The model reproduces every qualifying play’s original EP, and the raw next-possession EP reproduces recorded interception EPA.

Read immediate receiving field positions from **unfiltered** PBP, retaining no-play and penalty rows. A subsequent offensive penalty must not change the interception’s reported field position. The 2026 Rams play, for example, leaves LA at its own 43 even though its first valid offensive snap is from its own 38 after a separate penalty. Interception-return penalties reflected in the recorded EPA are included. A return touchdown is retained, uses its recorded scoring EPA, and fails the punt-like-field-position test. No qualifying return touchdowns occurred in this snapshot.

A punt-like field-position outcome leaves the opponent no more than 10 yards farther forward than the central modeled punt, or deeper. This is an outcome label, not an inclusion filter. A deficit of at least 0.50 EPA is an illustrative reporting threshold, not a statistical significance criterion; the Saints 2025 pick is −0.484 EPA versus the central benchmark.

Sensitivity scenarios use each modeled punt net distance minus/plus 10 yards, holding the 12-second elapsed time fixed. Separate time scenarios use 10 or 18 total seconds with central distance. These are illustrative scenario bounds, not confidence intervals. A hypothetical punt reaching the end zone becomes a touchback at the receiving 20; historical punt net distances already include touchbacks. The main comparison evaluates EP at typical modeled field position, **not expected EP integrated over a full punt-outcome distribution**. It does not separately simulate blocks, fumbles or return touchdowns on punts.

Central result: Allen’s actual −3.520 EPA versus −5.949 for incompletion/punt, a +2.429 total difference (+0.405 per interception). Other QBs’ −62.098 actual versus −46.365 hypothetical yields −15.733 total (−0.450 per pick). Stronger punts (+10 net yards each) change Allen’s difference to −1.417 total; weaker punts change it to +6.153. Only the **intercepted** subset is evaluated here. This does not estimate the expected value of the whole deep-shot strategy, which would require completions, failures, penalties and alternative available decisions. Small sample sizes and observed outcomes preclude a causal or optimality claim.


## Interpretive language and Allen quotation
The observed rates support an interpretation of higher risk tolerance; they do not establish an explicit conscious policy to trade interception risk against a likely punt. An Allen quote explicitly endorsing that policy was not verified. NFL.com’s September 12, 2023 report provides his comments after the Jets loss: he was not trying to throw interceptions and he criticized his forcing of the ball. The article preserves that context and does not treat those quotes as confirmation of an arm-punt strategy. Source: https://amp.nfl.com/news/bills-qb-josh-allen-after-4-turnover-game-vs-jets-i-am-the-reason-we-lost-tonigh


## October 14 editorial batch and short-pass outcome supplement
The main narrative now explains that the Rams’ +0.08 EPA advantage over the opening punt benchmark is practically negligible, driven by about 1.2 yards and five seconds of receiving-state difference. The longer hypothetical-punt sensitivity subsection and the redundant “What the Rams interception adds” section were removed from the article; scenario data remain in the outcome audit. One concise paragraph preserves the stronger-punt scenario and its modest total cost. Observed favorable outcomes do not eliminate return risk or establish the expected value of a future attempt. Receiver contested-catch ability, matchup, coverage and DPI upside are explicit parts of the stated tradeoff.

Historical context uses verified publisher metadata for the 1988 book and links the supplied Athletic retrospective; no unverified passage or quotation from the inaccessible full article is claimed. Publisher: https://press.uchicago.edu/ucp/books/book/chicago/H/bo196246388.html. Momentum is not described as unquantifiable: Johnson, Stimpson and Clark’s 2012 study found no statistically significant offensive carryover in matched first-quarter close-game drives, not universal proof that feelings never affect play. Primary paper: https://www.colorado.edu/faculty/johnson/sites/default/files/attached-files/92-big-plays-and-psychological-momentum-in-the-nfl.pdf.

The additional modern example is Drake Maye, 2025_15_BUF_NE, play2891: third-and25 at NE own42, 49 air yards, picked by White at BUF own9 with no return. It already qualifies in the all-interception audit. Official clip: https://www.buffalobills.com/video/tredavious-white-intercepts-drake-maye-bills-vs-patriots-highlights. YouTube’s public oEmbed response confirms the supplied compilation is “NFL \"Arm Punt\" Compilation” by Highlight Heaven, ID STUvyV4KCqE, and provides a standard iframe. Broad compilation labels are not substituted for the statistical third-down criteria.

Run `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python analysis/short_pass_outcomes.py` after `reproduce.py`. New `../data/short-pass-outcomes.json` includes completion and conversion counts, counts specifically among completions, EPA, charted-checkdown outcomes and throwaway counts for every QB. Same period, eligibility and NFL QB registry as the other analyses. The script joins official `complete_pass`, `first_down` and `touchdown` fields one-to-one; all 10,905 eligible pass attempts have completion data. It saves only source caches under the ignored .cache directory.

Allen: 100 short attempts, 72 completed, 35 converted; all 35 conversions came on completed throws (48.6% of completions). Other QBs: 4,776 short attempts, 3,486 completed, 1,062 converted; 1,040 conversions occurred among completed throws (29.8%). Accepted penalties can generate recorded first downs without a completed pass, hence the difference in conversion counts. Short completions can also improve fourth-down viability without immediately converting, so a failed third-down conversion is not automatically treated as an incorrect decision.

Rank clarification: Allen (3.17%), Love (1.74%) and Mahomes (1.72%) rank first through third for qualifying risk outcomes per likely-punt passing opportunity among >=100-attempt QBs. Risk conditional on taking a deep shot differs: 28.1%, 12.1% and 20.0%, respectively. These rankings do not establish conscious intent or strategic optimality.


## October 14 validation and robustness update

Run `python analysis/validate_thresholds.py` after generating the original caches. `data/validation-checks.json` records the frozen-model 3×3 threshold grid, seasonal checkdown coverage, a 2023-onward checkdown sensitivity, and distinct game/play keys for the repeated-looking interceptions. Allen ranks first under all nine definitions (70/80/90% punt probability; 5/10/15-yard allowed depth shortfall), with a 100-attempt qualification minimum recomputed for each scenario. This tests definition sensitivity, not intent or overall strategy value.

FTN records CHK in 2022: 2,803 normalized labels across charting and 355 among 2,572 eligible QB attempts. Allen has five in 67 eligible attempts. There are 46 missing read labels among 2022 eligible attempts, retained as unclassified rather than imputed. With 2022 excluded, Allen is second-lowest at 18/217 (8.29%) behind Purdy at 14/175 (8.00%).

The completed-short-pass conversion comparison is 35/72 (48.61%) versus 1,040/3,486 (29.83%). The other-QB 1,062/4,776 (22.24%) figure counts all converted short attempts, including conversions on noncompleted passes. The short-of-sticks baseline excluding Allen is 4,776/10,621 (44.97%); all eligible depths are known.

All 41 interception game/play keys are unique. Tua’s 2025_10_BUF_MIA plays 139 and 3001 and Mullens’ 2023_16_DET_MIN plays 1865 and 3529 independently match distinct raw PBP interception rows and EPA values. The article shows play IDs to distinguish them.

The Rams opener now uses the same field-position model as the full audit: 42.9609 net yards, Rams own 41.0391, punt-sequence EPA −1.27594 versus actual −1.20850, difference +0.06745. This supersedes the earlier league-average punt illustration. Giving every hypothetical punt ten extra net yards flips Allen’s aggregate advantage from +2.42888 to −1.41733 EPA; the article states the sign change explicitly.

This article evaluates risk-taking frequency and interception downside. It deliberately does not estimate the full upside of the 32 deep attempts or claim overall strategic optimality.


## Average interception cost scale reference

`python analysis/average_interception_cost.py` refreshes the 2022–2026 PBP releases and computes official QB interception EPA through October 12, excluding postseason, two-point attempts, nullified plays, spikes and kneels. It verifies unique game/play keys. `data/average-interception-cost.json` records all-QB and Allen-excluded results. Other QBs have 1,663 interceptions totaling −7,359.64973 EPA: −4.42553 per pick, or −26.55316 for six average picks. The article rounds these to −4.43 and −26.6. The illustrative −2.7 is six times a rounded −0.45 extra cost versus punting, whereas −26.6 is the full single-play EPA cost across all interception situations. It is a scale reference, not a matched estimate of strategic savings.

The article’s average-interception scale reference now includes Allen, using all 1,715 leaguewide QB interceptions: −4.39871 EPA per pick and −26.39224 for six average picks, rounded to −4.40 and −26.4. The other-QB average remains in the JSON for inspection. Allen’s six arm punts are still about 87% less costly on the same full-cost basis. The main likely-punt comparisons continue to exclude Allen from the other-QB baseline.
