from core.time_period.load_shape import BASE
from core.time_period.settlement_rules import AbstractSettlementRule, UKPowerSettlementRule, GasSettlementRule
from core.base.quantity import Unit, GBP, EUR, USD, PENCE, MWH, THERM, MMBTU


class AssetStatic(object):

    # create the dictionary for the Multiton patter
    instances = {}

    def __new__(cls, has_shape=False, has_intraday_shape=False, has_efa_day=False):
        try:
            cache = cls.instances[name.lower().strip()]
            assert cache.has_shape == has_shape
            assert cache.has_intraday_shape == has_intraday_shape
            assert cache.has_efa_day == has_efa_day
        except KeyError:
            new = super().__new__(cls)
            new.name = name
            new.has_shape = has_shape
            new.has_intraday_shape = has_intraday_shape
            new.has_efa_day = has_efa_day
            return new
        except AssertionError:
            raise ValueError("trying to assign multiple assets to the same name")

    def __str__(self):
        return self.name

    @property
    def load_shape(self):
        return BASE

    def __lt__(self, rhs):
        if self.name < rhs.name:
            return True
        return False


class CommodityStatic(AssetStatic):

    def __new__(cls, name, currency, settlement_rule, unit,
                has_shape=False, has_intraday_shape=False, has_efa_day=False):
        new = super().__new__(name, has_shape, has_intraday_shape, has_efa_day)
        assert isinstance(currency, Unit)
        assert isinstance(settlement_rule, AbstractSettlementRule)
        assert isinstance(unit, Unit)
        new.currency = currency
        new.settlement_rule = settlement_rule
        new.unit = unit
        return new

UKPOWER = CommodityStatic(currency = GBP,
                          settlement_rule = UKPowerSettlementRule(),
                          unit = GBP  / MWH,
                          has_shape = True,
                          has_intraday_shape = True,
                          has_efa_day = True)

DUTCHPOWER = CommodityStatic(currency = EUR,
                             settlement_rule = UKPowerSettlementRule(),
                             unit = EUR / MWH,
                             has_shape = True,
                             has_intraday_shape = True)

GERMANPOWER = CommodityStatic(currency = EUR,
                              settlement_rule = GasSettlementRule(),
                              unit = EUR / MWH,
                              has_shape = True,
                              has_intraday_shape = True)

NBP = CommodityStatic(currency = GBP,
                      settlement_rule = GasSettlementRule(),
                      unit = PENCE / THERM,
                      has_shape = True)

TTF = Commodity(currency = EUR,
                )


