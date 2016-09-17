import datetime as dt

from core.base.quantity import GBP
from core.forward_curves.fx_rates_forward_curves import DiscountCurve
from core.time_period.date_range import DateRange, LoadShapedDateRange


class MockDiscountCurve(DiscountCurve):

    def __init__(self, dates_to_df):
        self.data = dates_to_df
        self.currency = GBP

    def price(self, date):
        if isinstance(date, (DateRange, LoadShapedDateRange)):
            assert date.start == date.end
            date = date.start
        return self.data[date]

dates_to_df = {dt.date(2012, 11, 14): 0.995,
               dt.date(2012, 11, 20): 0.99,
               dt.date(2012, 12, 14): 0.985,
               dt.date(2012, 12, 20): 0.98,
               dt.date(2013, 1, 1): 0.979,
               dt.date(2013, 1, 4): 0.978,
               dt.date(2013, 1, 5): 0.977,
               dt.date(2013, 1, 6): 0.99,
               dt.date(2013, 1, 14): 0.975,
               dt.date(2013, 1, 20): 0.97,
               dt.date(2013, 2, 1): 0.95,
               dt.date(2013, 2, 20): 0.94,
               dt.date(2013, 3, 20): 0.93,
               dt.date(2013, 4, 20): 0.92,
               dt.date(2014, 1, 1): 0.90}

mock_discount_curve = MockDiscountCurve(dates_to_df)

class MockNullDiscountCurve(DiscountCurve):

    def __init__(self):
        self.currency = GBP

    @staticmethod
    def price(date):
        return 1

null_discount_curve = MockNullDiscountCurve()