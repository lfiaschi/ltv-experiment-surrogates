# Classical LTV figure specifications

Purpose: follow one classical fitted LTV model through a margin intervention.
No algorithm leaderboard. All quantitative values come from complete version3
`classical-results.json` with 500,000 training customers per refit.

## Classical model diagram

Source: BG/NBD counts and Gamma-Gamma conditional expected margin. Historical
RFM fits two components; updated RFM scores new experiments with fixed model
parameters. Predicted discounted purchases times predicted margin per purchase
is predicted future value. Required arrows: RFM to both model components; both
components to future value. Forbidden: assignment as a classical model input,
future outcomes as scoring inputs, Gamma-Gamma predicting dropout, BG/NBD
predicting money. Generate the entire diagram directly with Nano Banana Pro.
Use large type, white background, dark navy text and modest blue outlines.

## Calibration

Ten groups ranked by classical forecast on independent untreated customers.
Expected and predicted future value use the same week16→68 horizon. Show the
identity line, five refit averages, individual refit dots, shared axes. This is
customer calibration, not evidence of treatment-effect calibration.

## Duration example

Temporary and continuing rebate share exactly the same first4weeks and score.
Show paired predicted future lift once, and two true future effects (zero versus
20% of baseline). Also show RCT estimates separately if used, including their
sampling uncertainty. Do not label zero future lift as an unprofitable program;
early4week profit is positive. Dollar amounts are discounted to scoring time.

## Historical experiment check

Five independently simulated rebate sizes per refit; each has two coupled
future-duration policies. X-axis is treatment-minus-control early monetary RFM;
y-axis is future-margin effect. Same early RFM maps to different future effects.
No regression line claiming identification and no learned Meta-model result.

Source SVG width720. Essential labels >=38px, tick/secondary labels>=34px. At
318px displayed width these remain >=16.8/15px. Inspect actual desktop and375px
phone previews. Keep point labels separate, break long lines and use vertical
layouts instead of tiny text.
