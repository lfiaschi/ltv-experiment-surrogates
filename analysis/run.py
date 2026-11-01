"""A classical-LTV walkthrough, with no competing learned predictors."""

import argparse
import json
from pathlib import Path

import numpy as np
from model import (
    EARLY,
    FUTURE,
    PAST,
    advance,
    discounted_purchases,
    events,
    expected_margin,
    expected_value,
    fit,
    history,
    population,
    predict,
    remove_known_rebate,
)

OUT = Path(__file__).resolve().parents[1] / "results/classical-results.json"
UPLIFT = 0.20
HISTORICAL_DOSES = [0.05, 0.10, 0.20, 0.30, 0.40]


def contrast(values, treated):
    return float(values[treated].mean() - values[~treated].mean())


def contrast_se(values, treated):
    return float(
        np.sqrt(
            values[treated].var(ddof=1) / treated.sum()
            + values[~treated].var(ddof=1) / (~treated).sum()
        )
    )


def calibration(models, seed, n):
    rng = np.random.default_rng(seed)
    customers = population(rng, n)
    hist = history(customers, rng, PAST + EARLY)
    forecast = predict(models, hist)
    truth = expected_value(customers, hist.alive)
    actual = events(customers, rng, FUTURE, hist.alive)[3]
    groups = np.array_split(np.argsort(forecast), 10)
    return {
        "n": n,
        "prediction": float(forecast.mean()),
        "expected": float(truth.mean()),
        "realized": float(actual.mean()),
        "relative_bias": float(forecast.mean() / truth.mean() - 1),
        "bins": [
            {
                "prediction": float(forecast[g].mean()),
                "expected": float(truth[g].mean()),
                "realized": float(actual[g].mean()),
                "n": len(g),
            }
            for g in groups
        ],
    }


def trial(seed, n, uplift, models=None):
    rng = np.random.default_rng(seed)
    customers = population(rng, n)
    past = history(customers, rng)
    treated = rng.random(n) < 0.5
    early = events(customers, rng, EARLY, past.alive)
    base = advance(past, early)
    changed = advance(past, early, 1 + uplift)
    assigned = advance(past, early, 1 + uplift * treated)
    baseline_value = expected_value(customers, base.alive)
    realized = events(customers, rng, FUTURE, base.alive)[3]
    persistent_realized = realized * (1 + uplift * treated)
    temporary_rct = contrast(realized, treated)
    ongoing_rct = contrast(persistent_realized, treated)
    result = {
        "n": n,
        "uplift": uplift,
        "n_treated": int(treated.sum()),
        "frequency_contrast": contrast(assigned.frequency, treated),
        "recency_contrast": contrast(assigned.recency, treated),
        "monetary_contrast": contrast(assigned.monetary, treated),
        "paired_early_monetary_change": float(
            (changed.monetary - base.monetary).mean()
        ),
        "early_gain_per_treated": float(uplift * early[3][treated].mean()),
        "baseline_future_value": float(baseline_value.mean()),
        "temporary": {
            "expected_effect": 0.0,
            "realized_effect": temporary_rct,
            "se": contrast_se(realized, treated),
        },
        "continuing": {
            "expected_effect": float(uplift * baseline_value.mean()),
            "realized_effect": ongoing_rct,
            "se": contrast_se(persistent_realized, treated),
        },
        "rfm_identical_between_durations": True,
    }
    if models is not None:
        counts = discounted_purchases(models[0], base)
        value = counts * expected_margin(models[1], base)
        naive_changed = counts * expected_margin(models[1], changed)
        naive_assigned = np.where(treated, naive_changed, value)
        normalized = remove_known_rebate(past, assigned, uplift, treated)
        np.testing.assert_allclose(normalized.money, base.money, atol=1e-10)
        contract_value = counts * expected_margin(models[1], normalized)
        result.update(
            {
                "score_effect": contrast(naive_assigned, treated),
                "paired_score_effect": float((naive_changed - value).mean()),
                "score_se": contrast_se(naive_assigned, treated),
                "baseline_score_imbalance": contrast(value, treated),
                "contract_temporary_effect": contrast(contract_value, treated),
                "contract_continuing_effect": contrast(
                    contract_value * (1 + uplift * treated), treated
                ),
                "paired_contract_continuing_effect": float(
                    uplift * contract_value.mean()
                ),
                "paired_contract_temporary_effect": 0.0,
                "example_histories": [
                    {
                        "frequency": float(base.frequency[i]),
                        "recency": float(base.recency[i]),
                        "age": base.age,
                        "base_monetary": float(base.monetary[i]),
                        "early_orders": float(early[0][i]),
                        "changed_monetary": float(changed.monetary[i]),
                        "base_ltv": float(value[i]),
                        "changed_ltv": float(naive_changed[i]),
                    }
                    for i in np.flatnonzero(early[0] > 0)[:5]
                ],
            }
        )
        result["value_curve"] = [
            float(expected_value(customers, base.alive, h).mean() * uplift)
            for h in range(FUTURE + 1)
        ]
    return result


def run(
    repeats=5,
    train_n=500000,
    calibration_n=200000,
    test_n=50000,
    historical_n=20000,
    output=OUT,
):
    result = {
        "configuration": {
            "version": 3,
            "repeats": repeats,
            "train_n": train_n,
            "calibration_n": calibration_n,
            "test_n": test_n,
            "historical_n": historical_n,
            "past_weeks": PAST,
            "early_weeks": EARLY,
            "future_weeks": FUTURE,
            "uplift": UPLIFT,
            "historical_doses": HISTORICAL_DOSES,
            "monthly_discount": 0.01,
            "bg_truth": {"r": 0.8, "alpha": 4.0, "a": 2.5, "b": 8.0},
            "gg_truth": {"p": 6.0, "q": 4.0, "v": 15.0},
            "calibration_bias_tolerance": 0.03,
        },
        "runs": [],
    }
    output = Path(output)
    for rep in range(repeats):
        rng = np.random.default_rng(10000 + rep)
        customers = population(rng, train_n)
        train = history(customers, rng, PAST + EARLY)
        models = fit(train)
        row = {
            "rep": rep,
            "bg_parameters": models[0].params_.to_dict(),
            "gg_parameters": models[1].params_.to_dict(),
            "calibration": calibration(models, 20000 + rep, calibration_n),
            "experiment": trial(30000 + rep, test_n, UPLIFT, models),
            "historical": [
                trial(40000 + rep * 100 + i, historical_n, dose)
                for i, dose in enumerate(HISTORICAL_DOSES)
            ],
        }
        result["runs"].append(row)
        print(
            rep,
            "calibration bias",
            round(row["calibration"]["relative_bias"], 4),
            "score",
            round(row["experiment"]["score_effect"], 2),
            "true ongoing",
            round(row["experiment"]["continuing"]["expected_effect"], 2),
            flush=True,
        )
        output.with_suffix(".partial.json").write_text(
            json.dumps(result, indent=2) + "\n"
        )
    output.write_text(json.dumps(result, indent=2) + "\n")
    output.with_suffix(".partial.json").unlink(missing_ok=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--train-n", type=int, default=500000)
    parser.add_argument("--calibration-n", type=int, default=200000)
    parser.add_argument("--test-n", type=int, default=50000)
    parser.add_argument("--historical-n", type=int, default=20000)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    run(**vars(args))
