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
