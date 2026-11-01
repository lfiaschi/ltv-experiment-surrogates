"""One classical BG/NBD + Gamma-Gamma forecast and its matching process."""

from dataclasses import dataclass

import numpy as np
from lifetimes import BetaGeoFitter, GammaGammaFitter

PAST = 12.0
EARLY = 4.0
FUTURE = 52
DISCOUNT = np.log1p(0.01) * 12 / 52
SHAPE = 6.0


@dataclass
class Customers:
    rate: np.ndarray
    dropout: np.ndarray
    margin_rate: np.ndarray


@dataclass
class History:
    frequency: np.ndarray
    recency: np.ndarray
    money: np.ndarray
    alive: np.ndarray
    age: float

    @property
    def monetary(self):
        return np.divide(
            self.money,
            self.frequency,
            out=np.zeros_like(self.money),
            where=self.frequency > 0,
        )


def population(rng, n):
    return Customers(
        rng.gamma(0.8, 1 / 4, n), rng.beta(2.5, 8, n), rng.gamma(4, 1 / 15, n)
    )


def events(customers, rng, horizon, alive=None):
    """Simulate repeat purchases; the acquisition purchase at time zero is excluded."""
    n = len(customers.rate)
    active = np.ones(n, dtype=bool) if alive is None else alive.copy()
    end_alive = active.copy()
    clock = np.zeros(n)
    count, last, money, pv = [np.zeros(n) for _ in range(4)]
    while active.any():
        idx = np.flatnonzero(active)
        clock[idx] += rng.exponential(1 / customers.rate[idx])
        active[idx[clock[idx] > horizon]] = False
        bought = idx[clock[idx] <= horizon]
        if not len(bought):
            continue
        margin = rng.gamma(SHAPE, 1 / customers.margin_rate[bought])
        count[bought] += 1
        last[bought] = clock[bought]
        money[bought] += margin
        pv[bought] += margin * np.exp(-DISCOUNT * clock[bought])
        dead = bought[rng.random(len(bought)) < customers.dropout[bought]]
        active[dead] = False
        end_alive[dead] = False
    return count, last, money, pv, end_alive


def history(customers, rng, age=PAST):
    purchases = events(customers, rng, age)
    return History(purchases[0], purchases[1], purchases[2], purchases[4], age)


def advance(past, purchases, multiplier=1.0, horizon=EARLY):
    return History(
        past.frequency + purchases[0],
        np.where(purchases[0] > 0, past.age + purchases[1], past.recency),
        past.money + purchases[2] * multiplier,
        purchases[4],
        past.age + horizon,
    )


def remove_known_rebate(past, observed, uplift, treated):
    """Recover normal margins from observed records and known rebate terms."""
    observed_early_money = observed.money - past.money
    normal_money = past.money + observed_early_money / (1 + uplift * treated)
    return History(
        observed.frequency,
        observed.recency,
        normal_money,
        observed.alive,
        observed.age,
    )


def annuity(rate, horizon):
    return -np.expm1(-(rate + DISCOUNT) * horizon) / (rate + DISCOUNT)


def expected_value(customers, alive, horizon=FUTURE):
    return (
        alive
        * (SHAPE / customers.margin_rate)
        * customers.rate
        * annuity(customers.rate * customers.dropout, horizon)
    )


def fit(hist):
    bg = BetaGeoFitter(penalizer_coef=0.0).fit(
        hist.frequency, hist.recency, np.full(len(hist.frequency), hist.age)
    )
    repeat = hist.frequency > 0
    gg = GammaGammaFitter(penalizer_coef=0.0).fit(
        hist.frequency[repeat], hist.monetary[repeat], q_constraint=True
    )
    return bg, gg


def discounted_purchases(bg, hist, horizon=FUTURE):
    """Integrate the fitted count forecast with weekly midpoint discounting."""
    previous = np.zeros(len(hist.frequency))
    total = np.zeros_like(previous)
    for week in range(1, horizon + 1):
        cumulative = np.asarray(
            bg.conditional_expected_number_of_purchases_up_to_time(
                week, hist.frequency, hist.recency, hist.age
            )
        )
        total += (cumulative - previous) * np.exp(-DISCOUNT * (week - 0.5))
        previous = cumulative
    return total


def expected_margin(gg, hist):
    return np.asarray(
        gg.conditional_expected_average_profit(hist.frequency, hist.monetary)
    )


def predict(models, hist, horizon=FUTURE):
    bg, gg = models
    return discounted_purchases(bg, hist, horizon) * expected_margin(gg, hist)
