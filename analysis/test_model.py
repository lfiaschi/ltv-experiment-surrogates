import unittest

import numpy as np
from model import (
    EARLY,
    Customers,
    advance,
    events,
    expected_value,
    history,
    population,
    remove_known_rebate,
)


class ClassicalProcessChecks(unittest.TestCase):
    def test_recovery_uses_observed_margins_and_known_rebate(self):
        rng = np.random.default_rng(13)
        customers = population(rng, 3000)
        past = history(customers, rng)
        early = events(customers, rng, EARLY, past.alive)
        treated = rng.random(3000) < 0.5
        observed = advance(past, early, 1 + 0.2 * treated)
        recovered = remove_known_rebate(past, observed, 0.2, treated)
        normal = advance(past, early)
        np.testing.assert_allclose(recovered.money, normal.money, atol=1e-12)
        np.testing.assert_array_equal(recovered.frequency, observed.frequency)
        np.testing.assert_array_equal(recovered.recency, observed.recency)

    def test_rebate_preserves_rfm_counts_and_survival(self):
        rng = np.random.default_rng(14)
        customers = population(rng, 2000)
        past = history(customers, rng)
        early = events(customers, rng, EARLY, past.alive)
        base = advance(past, early)
        rebate = advance(past, early, 1.2)
        np.testing.assert_array_equal(base.frequency, rebate.frequency)
        np.testing.assert_array_equal(base.recency, rebate.recency)
        np.testing.assert_array_equal(base.alive, rebate.alive)
        np.testing.assert_allclose(
            rebate.money - base.money, 0.2 * early[2], atol=1e-12
        )
        self.assertTrue(np.all(base.frequency == np.floor(base.frequency)))
        self.assertTrue(np.all(base.recency <= base.age))

    def test_death_is_carried_between_windows(self):
        rng = np.random.default_rng(15)
        customers = population(rng, 10000)
        past = history(customers, rng)
        early = events(customers, rng, EARLY, past.alive)
        self.assertTrue(np.all(early[0][~past.alive] == 0))
        self.assertTrue(np.all(~early[4][~past.alive]))

    def test_expected_value_matches_transactions(self):
        rng = np.random.default_rng(16)
        customers = population(rng, 150000)
        past = history(customers, rng, 16)
        actual = events(customers, rng, 52, past.alive)[3]
        error = actual - expected_value(customers, past.alive)
        self.assertLess(abs(error.mean()), 4 * error.std() / np.sqrt(len(error)))

    def test_expected_value_horizon_endpoints(self):
        customers = Customers(np.array([0.2]), np.array([0.3]), np.array([0.25]))
        self.assertEqual(expected_value(customers, np.array([True]), 0)[0], 0)
        self.assertEqual(expected_value(customers, np.array([False]), 52)[0], 0)
        self.assertGreater(
            expected_value(customers, np.array([True]), 52)[0],
            expected_value(customers, np.array([True]), 4)[0],
        )


if __name__ == "__main__":
    unittest.main()
