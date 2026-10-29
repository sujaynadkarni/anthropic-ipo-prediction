"""Checks that the scraped data and the model reproduce the published results.

Run: python -m unittest
"""

import unittest

from valuation import inputs as I
from valuation import model as M


class ScrapedData(unittest.TestCase):
    def test_quarterly_revenue(self):
        self.assertEqual(I.LAST_QUARTER, "Q2 2026")
        self.assertAlmostEqual(I.QUARTERLY_REVENUE["Q2 2026"], 11.555)
        self.assertAlmostEqual(I.QUARTERLY_REVENUE["Q1 2025"], 0.376)

    def test_facts(self):
        self.assertAlmostEqual(I.FULLY_DILUTED_SHARES / 1e9, 16.94, places=2)
        self.assertAlmostEqual(I.SERIES_H_PRICE_PER_COMMON, 58.90, places=2)
        self.assertAlmostEqual(I.BROADCOM_LEASE_TOTAL, 161.2)
        self.assertAlmostEqual(I.USAGE_VIOLATION_HAIRCUT, 0.06)


class Model(unittest.TestCase):
    def test_base_case(self):
        lo, hi = M.fair_value_range(1.3)
        self.assertAlmostEqual(M.revenue_2027(1.3), 147.6, delta=0.5)
        self.assertAlmostEqual((lo + hi) / 2, 110, delta=1)

    def test_compute_ceiling_matches_assumption(self):
        self.assertAlmostEqual(M.compute_ceiling_growth(), I.GROWTH_SCENARIOS["compute ceiling"], delta=0.02)

    def test_lease_debt(self):
        self.assertAlmostEqual(M.broadcom_lease_debt(), 115, delta=1)


if __name__ == "__main__":
    unittest.main()
