from core.forward_curves.abstract_forward_curve import AbstractForwardPriceCurve
from core.forward_curves.quotes import FxQuotes
from core.forward_curves.quotes import MissingPriceError

import numpy as np
import datetime as dt


class FxForwardCurve(AbstractForwardPriceCurve):

    def __init__(self, quotes):
        super().__init__(quotes)
        assert isinstance(quotes, FxQuotes)
        self._prices = quotes.quotes
        self._dates = quotes.dates
        # pre-calculate the log forwards, since these are used in log-linear interpolation during each .price(period)
        # operation
        self._log_forwards = np.log(np.array([self._prices[date] for date in self._dates]))

    def price(self, period):
        if period not in self._prices:
            self._prices[period] = period.weighted_average_duration(self._one_day_price)
        return self._prices[period]

    def _one_day_price(self, date):
        date = date.start.toordinal()
        self._check_bounds(date)
        # use log-linear extrapolation to find the fx forward price
        return np.exp(np.interp(date, self._dates, self._log_forwards)) * self.unit

    def _check_bounds(self, date):
        if date < self._dates[0] or date > self._dates[-1]:
            raise MissingPriceError("Date requested ({})is outside the quoted period ({} to {})"
                                    .format(dt.date.fromordinal(date),
                                            dt.date.fromordinal(self._dates[0]),
                                            dt.date.fromordinal(self._dates[-1])))