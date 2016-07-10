from core.forward_curves.quotes import ContinuousQuotes
from core.quantity.quantity import UnitError, Quantity, GBP, PENCE
from core.time_period.date_range import LoadShapedDateRange, DateRange
from core.time_period.settlement_rules import GasSettlementRule

import unittest


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

    def test_init(self):
        with self.assertRaises(UnitError):
            ContinuousQuotes(self.mix_quantities_and_values, GasSettlementRule)
        with self.assertRaises(ValueError):
            ContinuousQuotes(self.mixed_date_range_types, GasSettlementRule)
        quantities = ContinuousQuotes(self.quantities, GasSettlementRule)
        self.assertEqual(quantities.unit, GBP)
        self.assertEqual(quantities.quotes, self.values)
        self.assertEqual(quantities, ContinuousQuotes(self.values, GasSettlementRule, GBP))
        self.assertEqual(quantities, ContinuousQuotes(self.mixed_quantities, GasSettlementRule))
        pence_quantities = ContinuousQuotes(self.quantities, GasSettlementRule, PENCE)
        self.assertEqual(pence_quantities.unit, PENCE)
        self.assertEqual(pence_quantities.quotes, self.pence_values)
        self.assertEqual(pence_quantities, ContinuousQuotes(self.pence_values, GasSettlementRule, PENCE))
        self.assertEqual(pence_quantities, ContinuousQuotes(self.mixed_quantities, GasSettlementRule, PENCE))


