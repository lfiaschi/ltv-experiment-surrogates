# Classical LTV as an experiment metric

Supporting code and figures for **LTV Models and the Value of Experimental Training** by Luca Fiaschi.

[Read the article preview](https://deploy-preview-90--capable-souffle-433eb5.netlify.app/blog/posts/ltv-experiment-surrogates/)

The example fits one BG/NBD + Gamma-Gamma model to ordinary transaction histories, then uses its predictions in a randomized experiment. A four-week supplier rebate and a continuing rebate create identical early RFM histories but different future margin. The study examines what historical experiments reveal about that missing duration information.

The Meta paper motivates the discussion of experimental training. These simulations check a classical forecast and a missing-duration example; they do not fit or benchmark Meta's two-stage estimator.

## Reproduce

Requirements: Python 3.13, [uv](https://docs.astral.sh/uv/), and Node.js 22.13 or newer. Python dependencies are pinned in `requirements.txt`; Node dependencies are locked in `package-lock.json`.

```sh
git clone https://github.com/lfiaschi/ltv-experiment-surrogates.git
cd ltv-experiment-surrogates

# Run the five process and valuation checks.
uv run --with-requirements requirements.txt \
  python -m unittest discover -s analysis -p 'test_*.py' -v

# Regenerate the complete simulation result.
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 \
uv run --with-requirements requirements.txt python analysis/run.py

# Regenerate the three quantitative figures from that result.
npm ci
npm run figures
```

The full run fits five independent simulations, each with 500,000 training customers, 200,000 calibration customers and 50,000 experimental customers. Five historical rebate sizes use another 20,000 customers each. `analysis/run.py --help` lists smaller sample sizes for quick checks. The final figures require the full configuration.

Results write to `results/classical-results.json`. An interrupted run leaves a separate `.partial.json` checkpoint and preserves the last complete result. Use `--output /tmp/results.json` for exploratory runs without replacing the checked-in results.

## Files

| Path | Contents |
| --- | --- |
| [`analysis/model.py`](analysis/model.py) | Transaction process, RFM summaries, fitted classical models and contract-aware valuation |
| [`analysis/run.py`](analysis/run.py) | Independent training/calibration cohorts and paired duration experiments |
| [`analysis/test_model.py`](analysis/test_model.py) | Process, survival, analytic-value and observable-reconstruction checks |
| [`results/classical-results.json`](results/classical-results.json) | All five fitted parameter sets, calibration groups, examples and effect estimates |
| [`scripts/generate-figures.mjs`](scripts/generate-figures.mjs) | Deterministic SVG/PNG charts from the results |
| [`scripts/generate-diagram.py`](scripts/generate-diagram.py) | Optional direct Gemini image generation for the model diagram |
| [`figures/`](figures/) | Published figures, diagram prompt and figure specifications |

## Interpretation

The target is contribution margin during the 52 weeks after the four-week scoring window, discounted to the scoring date at 1% per month. The temporary rebate earns positive early margin; its effect on this later target is zero.

| Mean across five refits | Dollars per customer |
| --- | ---: |
| Untreated-customer forecast | 51.68 |
| Untreated-customer expected value | 51.47 |
| Paired RFM-score lift, either rebate duration | 1.69 |
| True future lift, rebate expires | 0.00 |
| True future lift, rebate continues | 10.35 |
| Contract-aware classical forecast of continuing lift | 10.36 |

`paired_score_effect` compares each customer under both assignments. `score_effect` is the actual randomized treatment-minus-control mean and includes customer-composition noise. The duration scenarios share their early transactions; they are coupled counterfactuals, not independent replications.

## Model details

Customers begin alive at their initial purchase. Repeat purchases arrive at rate `lambda ~ Gamma(shape=0.8, rate=4)`. After each repeat, dropout occurs with probability `p ~ Beta(2.5, 8)`. Order margins follow `Gamma(shape=6, rate=nu)`, where `nu ~ Gamma(shape=4, rate=15)` independently of purchase and dropout parameters.

The models are fitted by maximum likelihood on 16-week untreated histories. Experimental customers have 12 weeks of prior history plus four experimental weeks. Their survival state carries across windows. Frequency and monetary summaries exclude the acquisition purchase.

The rebate raises margin per order by 20% without changing purchase rates, prices or dropout. The ordinary RFM forecast omits the known contract end date. The contract-aware calculation reconstructs ordinary margins from observed records and the known rebate multiplier, then values payments over the remaining term. It uses the same fitted models and no hidden customer parameters.

A pilot with smaller untreated samples produced 4.2% aggregate calibration error in one refit. Untreated sample sizes were increased uniformly while retaining the model, intervention settings and 3% calibration criterion. Every final refit's aggregate calibration bias is within 0.71%.

## Optional diagram generation

The model diagram and its prompt are checked in, so regenerating it is not required to reproduce the statistical results. To create a new version, set `GEMINI_API_KEY` in your local environment and run:

```sh
python scripts/generate-diagram.py

# Generate the experimental-training workflow from its own prompt.
python scripts/generate-diagram.py \
  --prompt figures/experimental-training-prompt.txt \
  --output figures/experimental-training-generated
```

The script uses the Gemini image model recorded for the original figure; `--model` can select an available model. It saves a new `classical-model-generated` image with the extension matching the returned format. Generated images can vary. Inspect their labels and arrows before publication. No API key is needed for the simulation or quantitative figures.

## Sources

- [Day et al., *Learning Robust, Long-run Surrogate Metrics with Modeling and Instrumental Variables*](https://doi.org/10.1145/3770854.3783922)
- [BG/NBD model](https://www.pymc-marketing.io/en/latest/notebooks/clv/bg_nbd.html)
- [Fader and Hardie's Gamma-Gamma model](https://www.brucehardie.com/notes/025/gamma_gamma.pdf)
