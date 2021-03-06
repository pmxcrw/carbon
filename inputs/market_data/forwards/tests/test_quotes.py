import datetime as dt
import unittest

import numpy as np

from core.base.quantity import UnitError, Quantity, GBP, PENCE, USD
from core.time_period.date_range import LoadShapedDateRange, DateRange
from core.time_period.settlement_rules import GasSettlementRule
from inputs.market_data.forwards.quotes import ContinuousQuotes, FxQuotes, RatesQuotes


class TestQuotes(unittest.TestCase):

    def setUp(self):
        self.mix_quantities_and_values = {LoadShapedDateRange("2016-M1", "Base"): Quantity(1, GBP),
                                          LoadShapedDateRange("2016", "Offpeak"): 2}
        self.mixed_date_range_types = {LoadShapedDateRange("2016-M1", "Base"): Quantity(1, GBP),
                                       DateRange("2016"): Quantity(2, GBP)}
        self.quantities = {LoadShapedDateRange("2016-M1", "Base"): Quantity(1, GBP),
                           LoadShapedDateRange("2016", "Offpeak"): Quantity(2, GBP)}
        self.values = {LoadShapedDateRange("2016-M1", "Base"): 1,
                           LoadShapedDateRange("2016", "Offpeak"): 2}
        self.mixed_quantities = {LoadShapedDateRange("2016-M1", "Base"): Quantity(1, GBP),
                                 LoadShapedDateRange("2016", "Offpeak"): Quantity(200, PENCE)}
        self.pence_values = {LoadShapedDateRange("2016-M1", "Base"): 100,
                       LoadShapedDateRange("2016", "Offpeak"): 200}

    def test_continuous_quotes(self):
        with self.assertRaises(UnitError):
            ContinuousQuotes(self.mix_quantities_and_values, GasSettlementRule)
        with self.assertRaises(ValueError):
            ContinuousQuotes(self.mixed_date_range_types, GasSettlementRule)
        quantities = ContinuousQuotes(self.quantities, GasSettlementRule)
        self.assertEqual(quantities.unit, GBP)
        self.assertEqual(quantities.price_dict, self.values)
        self.assertEqual(quantities, ContinuousQuotes(self.values, GasSettlementRule, GBP))
        self.assertEqual(quantities, ContinuousQuotes(self.mixed_quantities, GasSettlementRule))
        pence_quantities = ContinuousQuotes(self.quantities, GasSettlementRule, PENCE)
        self.assertEqual(pence_quantities.unit, PENCE)
        self.assertEqual(pence_quantities.price_dict, self.pence_values)
        self.assertEqual(pence_quantities, ContinuousQuotes(self.pence_values, GasSettlementRule, PENCE))
        self.assertEqual(pence_quantities, ContinuousQuotes(self.mixed_quantities, GasSettlementRule, PENCE))

    def test_fx_quotes(self):
        with self.assertRaises(TypeError):
            FxQuotes({DateRange("2016-Q1"): 2 * USD / GBP,
                      dt.date(2016, 5, 20): 1 * USD / GBP},
                     value_date=dt.date(2013, 12, 31))
        with self.assertRaises(TypeError):
            FxQuotes({LoadShapedDateRange("2016-Q1"): 2 * USD / GBP,
                      dt.date(2016, 5, 20): 1 * USD / GBP},
                     value_date=dt.date(2013, 12, 31))
        with self.assertRaises(TypeError):
            FxQuotes({LoadShapedDateRange("2016-05-20", "peak"): 2 * USD / GBP,
                     dt.date(1978, 5, 20): 1 * USD / GBP},
                     value_date=dt.date(2013, 12, 31))
        expected = {dt.date(2016, 5, 20).toordinal() - dt.date(2013, 12, 31).toordinal(): 1,
                    dt.date(2016, 6, 20).toordinal() - dt.date(2013, 12, 31).toordinal(): 2,
                    dt.date(2016, 7, 20).toordinal() - dt.date(2013, 12, 31).toordinal(): 3}
        test = FxQuotes({dt.date(2016, 5, 20): 1 * USD / GBP,
                         DateRange("2016-6-20"): 2 * USD / GBP,
                         LoadShapedDateRange("2016-7-20", "Base"): 3 * USD / GBP},
                        value_date=dt.date(2013, 12, 31))
        self.assertEqual(test.price_dict, expected)
        expected = np.array([dt.date(2016, 5, 20).toordinal() - dt.date(2013, 12, 31).toordinal(),
                             dt.date(2016, 6, 20).toordinal() - dt.date(2013, 12, 31).toordinal(),
                             dt.date(2016, 7, 20).toordinal() - dt.date(2013, 12, 31).toordinal()])
        self.assertTrue(all(test.dates == expected))

    def test_RatesQuotes(self):
        with self.assertRaises(TypeError):
            RatesQuotes(USD,
                        {dt.date(2016, 5, 20): 3 * GBP},
                        value_date=dt.date(2013, 12, 31))
        with self.assertRaises(TypeError):
            RatesQuotes(USD,
                        {DateRange("2016-Q1"): 0.2,
                         dt.date(2016, 5, 20): 0.1},
                        value_date=dt.date(2013, 12, 31))
        with self.assertRaises(TypeError):
            RatesQuotes(USD,
                        {LoadShapedDateRange("2016-Q1"): 0.2,
                         dt.date(2016, 5, 20): 0.1},
                        value_date=dt.date(2013, 12, 31))
        with self.assertRaises(TypeError):
            RatesQuotes(USD,
                        {LoadShapedDateRange("2016-05-20", "peak"): 2 * USD / GBP,
                         dt.date(1978, 5, 20): 1 * USD / GBP},
                        value_date=dt.date(2013, 12, 31))
        expected = {dt.date(2016, 5, 20).toordinal() - dt.date(2013, 12, 31).toordinal(): 0.1,
                    dt.date(2016, 6, 20).toordinal() - dt.date(2013, 12, 31).toordinal(): 0.2,
                    dt.date(2016, 7, 20).toordinal() - dt.date(2013, 12, 31).toordinal(): 0.3}
        test = RatesQuotes(USD,
                           {dt.date(2016, 5, 20): 0.1,
                            DateRange("2016-6-20"): 0.2,
                            LoadShapedDateRange("2016-7-20", "Base"): 0.3},
                           value_date=dt.date(2013, 12, 31))
        self.assertEqual(test.price_dict, expected)
        expected = np.array([dt.date(2016, 5, 20).toordinal() - dt.date(2013, 12, 31).toordinal(),
                             dt.date(2016, 6, 20).toordinal() - dt.date(2013, 12, 31).toordinal(),
                             dt.date(2016, 7, 20).toordinal() - dt.date(2013, 12, 31).toordinal()])
        self.assertTrue(all(test.dates == expected))