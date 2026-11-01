# Reported held-out experiment

Source: Day et al., Table4, DOI10.1145/3770854.3783922. The data file
`results/meta-holdouts.json` transcribes all five reported holdouts. The plot
shows Feed Holdout1: observed effect +0.283%, two-stage prediction +0.245%,
and direct-training prediction -0.100%. These are reported point estimates;
Table4 gives no uncertainty intervals.

Use a shared horizontal scale with a visible zero, direct labels and exact
percentage values. No inference of statistical significance. This is evidence
from Meta's product, not from the classical-LTV simulation in this repository.
The two-stage prediction is closer in four of the five reported cases; the
fifth has an observed zero and a slightly closer direct prediction.

Generate geometry and labels deterministically with `npm run paper-figure`.
