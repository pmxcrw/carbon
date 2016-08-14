from core.forward_curves.commodity_forward_curve import CommodityForwardCurve
from core.forward_curves.shape_ratio import ShapeAlgorithm
from core.forward_curves.quotes import MissingPriceError
from core.time_period.settlement_rules import GasSettlementRule, UKPowerSettlementRule
from core.forward_curves.daily_shape_calibration import SeasonBasedDailyShapeCalibration
from core.forward_curves.tests.mock_curves import mock_discount_curve, MockNullDiscountCurve
from core.quantity.quantity import PENCE, THERM, GBP, MWH, DAY
from core.time_period.date_range import DateRange, LoadShapedDateRange, NEVER_LSDR, NEVER_DR
from core.time_period.load_shape import BASE, PEAK, OFFPEAK, NEVER_LS, WEEKEND, WEEKDAY
from core.forward_curves.quotes import ContinuousQuotes

import datetime as dt
import unittest

class CommodityForwardCurveTest(unittest.TestCase):

    def test_price_outside_daterange(self):
        quotes = ContinuousQuotes({LoadShapedDateRange("2013-M1", BASE): 75 * PENCE / THERM,
                                   LoadShapedDateRange("2013-M2", BASE): 80 * PENCE / THERM}, GasSettlementRule)
        curve = CommodityForwardCurve(quotes, mock_discount_curve)
        with self.assertRaises(MissingPriceError):
            curve.price(LoadShapedDateRange("2013-Q1", BASE))

    def test_no_quotes(self):
        with self.assertRaises(MissingPriceError):
            CommodityForwardCurve(ContinuousQuotes({}, GasSettlementRule), mock_discount_curve, ShapeAlgorithm)

    def test_gas_price_with_DR(self):
        quotes = ContinuousQuotes({DateRange("2012-Q4"): 9 * PENCE / THERM,
                                   DateRange("2012-M12"): 12 * PENCE / THERM}, GasSettlementRule)
        curve = CommodityForwardCurve(quotes, MockNullDiscountCurve())
        nov_12 = DateRange("2012-M11")
        nov_price = curve.price(nov_12)
        # x*61+12*31=92*9 => x = (92*9-12*31)/61 = 7.4754
        self.assertAlmostEqual(nov_price.value, 7.4754, 2)
        self.assertEqual(nov_price.unit, PENCE / THERM)
        overlapping = DateRange(dt.date(2012, 11, 30), dt.date(2012, 12, 2))
        # y = (1*7.4754+2*12)/3 = 10.492
        overlapping_price = curve.price(overlapping)
        self.assertAlmostEqual(overlapping_price.value, 10.492, 3)
        with self.assertRaises(MissingPriceError):
            curve.price(DateRange("2016"))

    def test_gas_price_with_LSDR(self):
        quotes = ContinuousQuotes({LoadShapedDateRange("2012-Q4", BASE): 9 * PENCE / THERM,
                                   LoadShapedDateRange("2012-M12", BASE): 12 * PENCE / THERM}, GasSettlementRule)
        curve = CommodityForwardCurve(quotes, MockNullDiscountCurve())
        nov_12 = LoadShapedDateRange("2012-M11", BASE)
        nov_price = curve.price(nov_12)
        # x*61+12*31=92*9 => x = (92*9-12*31)/61 = 7.4754
        self.assertAlmostEqual(nov_price.value, 7.4754, 2)
        overlapping = DateRange(dt.date(2012, 11, 30), dt.date(2012, 12, 2))
        # y = (1*7.4754+2*12)/3 = 10.492
        overlapping_price = curve.price(overlapping)
        self.assertAlmostEqual(overlapping_price.value, 10.492, 3)
        with self.assertRaises(MissingPriceError):
            curve.price(DateRange("2016"))

    def test_power_pice(self):
        dec_12_base = LoadShapedDateRange("2012-M12", BASE)
        dec_12_peak = LoadShapedDateRange("2012-M12", PEAK)
        quotes = ContinuousQuotes({dec_12_base: 90 * GBP / MWH, dec_12_peak: 120 * GBP / MWH}, UKPowerSettlementRule)
        curve = CommodityForwardCurve(quotes, MockNullDiscountCurve())
        dec_12_offpeak = LoadShapedDateRange("2012-M12", OFFPEAK)
        price = curve.price(dec_12_offpeak)
        OFFPEAK_price = (quotes.quotes[dec_12_base] * dec_12_base.duration -
                         quotes.quotes[dec_12_peak] * dec_12_peak.duration) / dec_12_offpeak.duration
        self.assertAlmostEqual(price.value, OFFPEAK_price)

    def test_gas_price_with_discount_curve(self):
        q4_12 = DateRange("2012-Q4")
        dec_12 = DateRange("2012-M12")
        quotes = ContinuousQuotes({q4_12: 9 * PENCE / THERM, dec_12: 12 * PENCE / THERM}, GasSettlementRule)
        curve = CommodityForwardCurve(quotes, mock_discount_curve)
        self.assertAlmostEqual(curve.price(q4_12).value, 9)

        q4_dur = q4_12.discounted_duration(GasSettlementRule, mock_discount_curve)
        dec_dur = dec_12.discounted_duration(GasSettlementRule, mock_discount_curve)
        expected_price = (q4_dur * 9 - dec_dur * 12) / (q4_dur - dec_dur)
        nov_12_price = curve.price(DateRange("2012-M11")).value
        self.assertAlmostEqual(nov_12_price, expected_price)

        overlapping = DateRange(dt.date(2012, 11, 30), dt.date(2012, 12, 2))
        nov_df = mock_discount_curve.price(dt.date(2012, 12, 20))
        dec_df = mock_discount_curve.price(dt.date(2013, 1, 20))
        expected = (1 * nov_12_price * nov_df + 2 * 12 * dec_df) / (1 * nov_df + 2 * dec_df)
        overlapping_price = curve.price(overlapping)
        self.assertAlmostEqual(overlapping_price.value, expected, 3)

    def test_gas_within_month(self):
        """
        Test the curve shaping iwthin month, when no scalars are involved, but with a non trivial intersection of
        weekend and BOM
        """
        da = DateRange("2012-1-26")
        wend = DateRange(dt.date(2012, 1, 28), dt.date(2012, 1, 29))
        bom = DateRange(dt.date(2012, 1, 27), dt.date(2012, 1, 31))
        quotes = ContinuousQuotes({da: 54.5, wend: 54.4, bom: 54.3}, GasSettlementRule, PENCE / THERM)
        curve = CommodityForwardCurve(quotes, MockNullDiscountCurve)

        residual_bom = (5 * 54.3 - 2 * 54.4) / 3

        self.assertAlmostEqual(curve.price(da).value, 54.5)
        self.assertAlmostEqual(curve.price(DateRange("2012-1-27")).value, residual_bom)
        self.assertAlmostEqual(curve.price(DateRange("2012-1-28")).value, 54.4)
        self.assertAlmostEqual(curve.price(DateRange("2012-1-29")).value, 54.4)
        self.assertAlmostEqual(curve.price(DateRange("2012-1-30")).value, residual_bom)
        self.assertAlmostEqual(curve.price(DateRange("2012-1-31")).value, residual_bom)

    def test_gas_with_shaping(self):
        s_to_q = {BASE: [1.1, 0.9, 1, 1]}
        q_to_m = {BASE: [1.2, 1.2, 0.6, 1.1, 1, 0.9, 1, 1, 1, 1, 1, 1]}
        wdwe = {WEEKDAY: 1.0, WEEKEND: 1.0}
        base_ratios = SeasonBasedDailyShapeCalibration(s_to_q, q_to_m, wdwe)
        quotes = ContinuousQuotes({DateRange("2010-WIN"): 100,
                                   DateRange("2011-Q1"): 105,
                                   DateRange("2011-SUM"): 90}, GasSettlementRule, PENCE / THERM)
        curve = CommodityForwardCurve(quotes, MockNullDiscountCurve(), base_ratios)

        season_price= curve.price(DateRange("2011-SUM"))
        self.assertAlmostEqual(season_price.value, 90)

        # check ratios
        q2_price = curve.price(DateRange("2011-Q2"))
        q3_price = curve.price(DateRange("2011-Q3"))
        self.assertAlmostEqual(q2_price / q3_price, 0.9)

        # check shaping doesn't happen
        q1_price = curve.price(DateRange("2011-Q1"))
        self.assertAlmostEqual(q1_price.value, 105)

        # monthly shaping test
        months = DateRange("2011-Q1").split_by_month
        prices = [curve.price(month) for month in months]
        durations = [month.duration for month in months]
        q1_norm = sum(durations) / sum([duration * ratio for duration, ratio in zip(durations, q_to_m[BASE][0:3])])
        for price, ratio in zip(prices, q_to_m[BASE][0:3]):
            self.assertAlmostEqual(price / q1_price, ratio * q1_norm)

    def test_gas_within_month_with_scalars(self):
        """
        Test the curve shaping within month, when scalars are involved, with a non-trivial intersection of WEND and BOM
        """
        da = DateRange("2012-1-3")
        wend = DateRange(dt.date(2012, 1, 7), dt.date(2012, 1, 8))
        bom = DateRange(dt.date(2012, 1, 4), dt.date(2012, 1, 31))
        quotes = ContinuousQuotes({da: 54.5, wend: 54.4, bom: 54.3}, GasSettlementRule, PENCE / THERM)

        s_to_q = {BASE: [1.1, 0.9, 1, 1]}
        q_to_m = {BASE: [1.2, 1.2, 0.6, 1.1, 1, 0.9, 1, 1, 1, 1, 1, 1]}
        wdwe = {WEEKDAY: 1.1, WEEKEND: 1.0}
        base_ratios = SeasonBasedDailyShapeCalibration(s_to_q, q_to_m, wdwe)

        curve = CommodityForwardCurve(quotes, MockNullDiscountCurve, base_ratios)

        # 1) Check that the quotes of the quoted shapes are arbitrage free
        self.assertAlmostEqual(curve.price(DateRange("2012-1-3")).value, 54.5)
        self.assertAlmostEqual(curve.price(DateRange("2012-1-7")).value, 54.4)
        self.assertAlmostEqual(curve.price(DateRange("2012-1-8")).value, 54.4)

        # 2) Check weekday /w eekend ratio is applied within BOM
        weekday_price = curve.price(DateRange("2012-1-27"))
        weekend_price = curve.price(DateRange("2012-1-28"))
        self.assertAlmostEqual(weekday_price / weekend_price, 1.1, 12)

        # 3) Check weekday / weekend ratio as applied across BOM and the quotes week-end
        weekend_price2 = curve.price(DateRange(dt.date(2012, 1, 4), dt.date(2012, 1, 6)))
        self.assertAlmostEqual(weekday_price.value, weekend_price2.value, 12)

        # 4) Recompute the BOM price from the price of each day - i.e. check that daily prices are arb free
        bom_price = 0
        for day in bom:
            bom_price += curve.price(day) * DAY
        bom_price /= bom.duration
        self.assertAlmostEqual(bom_price.value, 54.3, 12)

        # 5) Directly request BOM price, i.e. check that BOM price is arbitrage free
        self.assertAlmostEqual(bom_price, curve.price(bom), 12)

