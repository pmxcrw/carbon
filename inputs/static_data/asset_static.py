from core.time_period.load_shape import BASE
from core.time_period.settlement_rules import AbstractSettlementRule, UKPowerSettlementRule, GasSettlementRule
from core.base.quantity import Unit, GBP, EUR, USD, PENCE, MWH, THERM, MMBTU


class AssetStatic(object):

    def __init__(self, has_shape=False, has_intraday_shape=False, has_efa_day=False):
        self.has_shape = has_shape
        self.has_intraday_shape = has_intraday_shape
        self.has_efa_day = has_efa_day

    @property
    def load_shape(self):
        return BASE


class CommodityStatic(AssetStatic):

    def __init__(self, currency, settlement_rule, unit, has_shape=False, has_intraday_shape=False, has_efa_day=False):
        super().__init__(has_shape, has_intraday_shape, has_efa_day)
        assert isinstance(currency, Unit)
        assert isinstance(settlement_rule, AbstractSettlementRule)
        assert isinstance(unit, Unit)
        self.currency = currency
        self.settlement_rule = settlement_rule
        self.unit = unit

UKPOWER = CommodityStatic(currency=GBP,
                          settlement_rule=UKPowerSettlementRule(),
                          unit=GBP / MWH,
                          has_shape=True,
                          has_intraday_shape=True,
                          has_efa_day=True)

DUTCHPOWER = CommodityStatic(currency=EUR,
                             settlement_rule=UKPowerSettlementRule(),
                             unit=EUR / MWH,
                             has_shape=True,
                             has_intraday_shape=True)

GERMANPOWER = CommodityStatic(currency=EUR,
                              settlement_rule=GasSettlementRule(),
                              unit=EUR / MWH,
                              has_shape=True,
                              has_intraday_shape=True)

NBP = CommodityStatic(currency=GBP,
                      settlement_rule=GasSettlementRule(),
                      unit=PENCE / THERM,
                      has_shape=True)

TTF = CommodityStatic(currency=EUR,
                      settlement_rule=GasSettlementRule(),
                      unit=EUR / MWH,
                      has_shape=True)

HENRYHUB = CommodityStatic(currency=USD,
                           settlement_rule=GasSettlementRule(),
                           )