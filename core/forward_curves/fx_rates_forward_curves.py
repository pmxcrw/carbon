import datetime as dt

import numpy as np

from core.forward_curves.abstract_forward_curve import AbstractDailyForwardCurve, AbstractForwardCurve
from core.time_period.date_range import DateRange, LoadShapedDateRange
from inputs.market_data.forwards.quotes import FxQuotes, RatesQuotes
from inputs.static_data.time_constants import DAYS_PER_YEAR


class FxForwardCurve(AbstractDailyForwardCurve):

    def __init__(self, quotes):
        if not isinstance(quotes, FxQuotes):
            raise TypeError("price_dict must be FXQuotes: {} provided".format(type(quotes)))
        super().__init__(quotes)
        self.unit = quotes.unit
        # pre-calculate the log forwards, since these are used in log-linear interpolation during each .price(period)
        # operation
        self._log_forwards = np.log(np.array([quotes[date] for date in self._dates]))

    def _new_price(self, period):
        if period not in self._cache:
            self._cache[period] = period.weighted_average_duration(self._one_day_price)
        return self._cache[period]

    def _one_day_price(self, date):
        date = date.start.toordinal() - self.value_date
        self._check_bounds(date)
        # use log-linear extrapolation to find the fx forward price
        return np.exp(np.interp(date, self._dates, self._log_forwards)) * self.unit

    @property
    def inverse(self):
        return InverseFxForwardCurve(self)


class InverseFxForwardCurve(AbstractForwardCurve):

    def __init__(self, fx_curve):
        super().__init__()
        self._fx_curve = fx_curve
        self.unit = fx_curve.unit.inverse
        self.value_date = fx_curve.value_date

    def _new_price(self, period):
        return 1 / self._fx_curve.price(period)


class DiscountCurve(AbstractDailyForwardCurve):

    """
    A discount curve depends on a collection of price_dict from an actuarial Yield Curve.

    Given a yield curve date t0, a discount factor is calculated as:

        B(tau) = 1 / (1 + r(tau)) ^ tau / 365

    where tau = (t - t0). We assume the daycount convention is ACT / 365.

    The forward discount factor (from t1 to t2) is calculated a B(t2 - t0) / B(t1 - t0)
    """

    def __init__(self, quotes):
        if not isinstance(quotes, RatesQuotes):
            raise TypeError("price_dict must be RatesQuotes: {} provided".format(type(quotes)))
        super().__init__(quotes)
        # interpolation of the yield curve is linear (unlike forward curve)
        self._rates = np.array([quotes[date] for date in self._dates])
        self.currency = quotes.currency

    @property
    def is_null(self):
        return all(self._rates == 0)

    def _parse_time_period(self, delivery_period):
        if isinstance(delivery_period, int):
            return delivery_period
        if isinstance(delivery_period, dt.date):
            return delivery_period.toordinal()
        if isinstance(delivery_period, (DateRange, LoadShapedDateRange)):
            if delivery_period.start == delivery_period.end:
                return delivery_period.start.toordinal()
            else:
                raise TypeError("DiscountCurve can only price a single day: {} provided".format(delivery_period))
        raise TypeError("delivery_period: {} cannot be parsed into an ordinal date".format(delivery_period))

    def _new_price(self, period):
        if period == self.value_date:
            return 1
        tau = period - self.value_date
        self._check_bounds(tau)
        rate = np.interp(tau, self._dates, self._rates)
        return (1 + rate) ** (- tau / DAYS_PER_YEAR)

    def forward_price(self, period):
        return self.price(period.end) / self.price(period.start)


class ForeignDiscountCurve(AbstractForwardCurve):

    """
    A foreign discount curve depends on a domestic DiscountCurve and an FxForwardCurve

    Given a curve date t0 a foreign discount factor is calculated as:

        B(t2 - t1) = B(t2 - t1) * Fx(t2) / Fx(t1)
    """

    def __init__(self, domestic_curve, fx_curve):
        super().__init__()
        if domestic_curve.currency != fx_curve.unit.denominator:
            if domestic_curve.currency == fx_curve.unit.numerator:
                fx_curve = fx_curve.inverse
            else:
                raise TypeError("fx curve has units {} so is incompatible with the domestic curve in {}"
                                .format(fx_curve.unit, domestic_curve.currency))
        self.currency = fx_curve.unit * domestic_curve.currency
        if domestic_curve.value_date != fx_curve.value_date:
            raise TypeError("fx curve has value date {} which is incompatible with domestic curve: {}"
                            .format(fx_curve.value_date, domestic_curve.value_date))
        self.value_date = domestic_curve.value_date
        self._domestic_curve = domestic_curve
        self._fx_curve = fx_curve
        self._spot_fx = fx_curve.price(self.value_date)

    def _new_price(self, period):
        domestic_df = self._domestic_curve.price(period)
        forward_fx = self._fx_curve.price(period)
        return self._spot_fx * domestic_df / forward_fx
