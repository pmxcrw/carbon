from core.quantity.quantity import UnitError, _AbstractUnit, _BaseUnit, _DerivedUnit, Unit, Quantity, \
    _MWH, MWH, _THERM, THERM, DAY, HOUR, MW, _TONNE, TONNE, MMBTU, KWH, MTHERM, _BBL, BBL, \
    _PENCE, PENCE, _GBP, GBP, _EUR, EUR, _USD, USD, MWH_PER_THERM, \
    mean, ones, array, amax, empty, reshape, concatenate, var, floor, ceil, arange, zeros, maximum, minimum

import numpy as np
import unittest


class TestAbstractUnits(unittest.TestCase):

    def setUp(self):
        self.xyz = _AbstractUnit('xyz', 1)
        self.zyx = _AbstractUnit('zyx', 1)

    def test_new(self):
        self.assertEqual(self.xyz.name, 'xyz')
        self.assertEqual(self.xyz.base_multiplier, 1)

    def test_multiton(self):
        with self.assertRaises(UnitError):
            _AbstractUnit('xyz', 100)

    def test_conversion_factor(self):
        with self.assertRaises(NotImplementedError):
            self.xyz.conversion_factor(self.zyx)

    def test_eq(self):
        self.assertNotEqual(self.xyz, _AbstractUnit('abc', 100))

    def test_lt(self):
        self.assertLess(self.xyz, self.zyx)


class TestBaseUnits(unittest.TestCase):

    def test_new(self):
        self.assertEqual(_USD.name, 'USD')
        self.assertEqual(_USD.base_multiplier, 1)
        with self.assertRaises(AssertionError):
            _BaseUnit('cad_cent', 100)

    def test_reference_unit(self):
        self.assertEqual(_USD.reference_unit, _USD)


class TestDerivedUnits(unittest.TestCase):

    def setUp(self):
        self.cents = _DerivedUnit('cents', 100, 'usd')
        self.cad = _BaseUnit('cad', 1)
        self.cad_cents = _DerivedUnit('cad_cents', 100, self.cad)

    def test_new(self):
        self.assertEqual(self.cents.name, 'cents')
        self.assertEqual(self.cents.base_multiplier, 100)

    def test_parse_base_unit(self):
        litres = _DerivedUnit('litres', 1000, 'milliliters')
        with self.assertRaises(UnitError):
            _DerivedUnit('milliliters', 0.001, litres)

    def test_conversion_factor(self):
        litres = _DerivedUnit('litres', 1000, 'milliliters')
        centilitres = _DerivedUnit('centileters', 10, 'milliliters')
        self.assertEqual(litres.conversion_factor(centilitres), 100)


class TestUnits(unittest.TestCase):

    def setUp(self):
        self.cents = _DerivedUnit('cents', 100, 'usd')
        self.cad = _BaseUnit('cad', 1)
        self.cad_cents = _DerivedUnit('cad_cents', 100, self.cad)
        self.jpy = _BaseUnit('jpy', 1)
        self.aud = _BaseUnit('aud', 1)

    def test_degeneracy(self):
        with self.assertRaises(UnitError):
            Unit([_USD, _GBP, _PENCE], [1, 2, -1])

    def test_no_repeats(self):
        test_unit = Unit([_USD, _PENCE, self.cad, _EUR], [1, 1, -1, 2])
        self.assertEqual(test_unit.units, (_EUR, _PENCE, _USD, self.cad))
        self.assertEqual(test_unit.exponents, (2, 1, 1, -1))

    def test_no_repeats_with_zeros(self):
        test_unit = Unit([self.jpy, _PENCE, self.cad, _EUR, self.cents], [1, 1, -1, 0, 2])
        self.assertEqual(test_unit.units, (_PENCE, self.cad, self.cents, self.jpy))
        self.assertEqual(test_unit.exponents, (1, -1, 2, 1))

    def test_repeats_no_zeros(self):
        test_unit = Unit([self.cad, self.jpy, _PENCE, self.cad, _PENCE], [1, 1, 1, 1, 3])
        self.assertEqual(test_unit.units, (_PENCE, self.cad, self.jpy))
        self.assertEqual(test_unit.exponents, (4, 2, 1))

    def test_repeats_easy_zero(self):
        test_unit = Unit([self.cad, self.aud, self.jpy, _PENCE, self.cad, _PENCE], [1, 0, 1, 1, 1, 3])
        self.assertEqual(test_unit.units, (_PENCE, self.cad, self.jpy))
        self.assertEqual(test_unit.exponents, (4, 2, 1))

    def test_repeats_cancelling_unit(self):
        test_unit = Unit([self.cad, self.aud, self.jpy, _PENCE, self.cad, _PENCE], [1, 0, 1, 1, -1, 3])
        self.assertEqual(test_unit.units, (_PENCE, self.jpy))
        self.assertEqual(test_unit.exponents, (4, 1))

    def test_empty(self):
        with self.assertRaises(UnitError):
            Unit([], [])

    def test_parse(self):
        self.assertEqual(Unit("USD.GBP^2 / BBL^3.EUR"), Unit((_BBL, _USD, _GBP, _EUR), (-3, 1, 2, -1)))
        self.assertEqual(Unit("MWH/(BBL^2.TONNE^3)"), Unit((_MWH, _BBL, _TONNE), (1, -2, -3)))
        self.assertEqual(Unit("(MWH^2.TONNE) /(BBL^3)"), Unit((_MWH, _TONNE, _BBL), (2, 1, -3)))
        with self.assertRaises(UnitError):
            Unit("USD / USD")
        with self.assertRaises(ValueError):
            Unit("MWH/(BBL^2.TONNE^3")
        with self.assertRaises(ValueError):
            Unit("(MWH^3.TONNE/BBL)")
        with self.assertRaises(UnitError):
            Unit("")
        with self.assertRaises(UnitError):
            Unit(" ")

    def test_standardise(self):
        lhs = Unit("PENCE / THERM")
        rhs = Unit("GBP / THERM")
        self.assertEqual(Unit.standardise(lhs, rhs), (Quantity(0.01, rhs), Quantity(1, rhs)))
        rhs = Unit("GBP / MWH")
        self.assertEqual(Unit.standardise(lhs, rhs), (Quantity(0.01 / MWH_PER_THERM, rhs), Quantity(1, rhs)))
        rhs = Unit("USD / BBL")
        self.assertEqual(Unit.standardise(lhs, rhs), (Quantity(1, lhs), Quantity(1, rhs)))

    def test_reference_unit(self):
        self.assertEqual(Unit("PENCE / THERM").reference_unit, Quantity(0.01 / MWH_PER_THERM, Unit("GBP / MWH")))

    def test_multiply(self):
        self.assertEqual(Unit("PENCE / THERM") * THERM, PENCE)
        self.assertEqual(Unit("PENCE / THERM") * PENCE, Unit("PENCE^2 / THERM"))
        self.assertEqual(Unit("PENCE / THERM") * MWH, Quantity(1/MWH_PER_THERM, PENCE))
        self.assertEqual(MWH * Unit("PENCE / THERM") * MWH, Quantity(1/MWH_PER_THERM, Unit("PENCE.MWH")))
        self.assertEqual(GBP * Unit("MWH / PENCE"), Quantity(100, MWH))
        self.assertEqual(GBP * 10, Quantity(10, GBP))
        self.assertEqual(10 * GBP, Quantity(10, GBP))
        self.assertEqual(Quantity(10, GBP) * Unit("PENCE / THERM"), Quantity(0.1, Unit("GBP^2 / THERM")))
        self.assertEqual(Unit("PENCE / THERM") * Quantity(10, GBP), Quantity(0.1, Unit("GBP^2 / THERM")))
        self.assertEqual(Unit("1/PENCE") * Unit("GBP"), 100)
        self.assertEqual(THERM * THERM, Unit("THERM^2"))

    def test_divide(self):
        self.assertEqual(Unit("PENCE /THERM") / PENCE, Unit("1/THERM"))
        self.assertEqual(Unit("PENCE / THERM") / THERM, Unit("PENCE / THERM^2"))
        self.assertEqual(Unit("PENCE/THERM") / MWH, Quantity(1/MWH_PER_THERM, Unit("PENCE/MWH^2")))
        self.assertEqual(MWH / Unit("PENCE / THERM"), Quantity(MWH_PER_THERM, Unit("MWH^2/PENCE")))
        self.assertEqual(GBP / Unit("MWH / PENCE"), Quantity(0.01, Unit("GBP^2/MWH")))
        self.assertEqual(GBP / 100, Quantity(0.01, GBP))
        self.assertEqual(100 / GBP, Quantity(100, GBP.inverse))
        self.assertEqual(Quantity(10, GBP) / Unit("PENCE / THERM"), Quantity(1000, THERM))
        self.assertEqual(Unit("PENCE / THERM") / Quantity(10, GBP), Quantity(0.001, Unit("1/THERM")))
        self.assertEqual(Unit("PENCE")/Unit("THERM"), Unit("PENCE/THERM"))
        self.assertEqual(Unit("PENCE") / Unit("GBP"), 0.01)
        a = 1 / DAY
        self.assertEqual(type(a), type(1 * DAY))
        self.assertEqual(1 / a, 1 * DAY)

    def test_inverse(self):
        self.assertEqual(Unit("PENCE/THERM"), Unit("THERM/PENCE").inverse)

    def test_equals(self):
        self.assertEqual(Unit("PENCE/THERM"), Unit((_THERM, _PENCE), (-1, 1)))
        self.assertEqual(Unit((_THERM, _PENCE), (-1, 1)), Unit((_PENCE, _THERM), (1, -1)))

    def test_str(self):
        self.assertEqual(str(Unit((_THERM, _PENCE), (-1, 1))), "PENCE / THERM")
        self.assertEqual(str(Unit((_THERM, _PENCE, _BBL), (-1, 1, -2))), "PENCE / (BBL^2.THERM)")
        self.assertEqual(str(Unit((_THERM, _PENCE), (-2, 4))), "PENCE^4 / THERM^2")
        self.assertEqual(str(Unit([_THERM], [-1])), "1 / THERM")

    def test_conversion_factor(self):
        self.assertEqual(MWH_PER_THERM, THERM.conversion_factor(MWH))
        with self.assertRaises(UnitError):
            MWH.conversion_factor(BBL)
        self.assertEqual(1 / 1000, KWH.conversion_factor(MWH))
        self.assertEqual(1e6, MTHERM.conversion_factor(THERM))

    def test_equivalent(self):
        self.assertTrue(THERM.equivalent(MWH))
        self.assertTrue(MWH.equivalent(THERM))
        self.assertFalse(MWH.equivalent(BBL))

    def test_name(self):
        ppt = PENCE / THERM
        self.assertEqual(ppt.name, "PENCE / THERM")

    def test_unit_identity(self):
        a = Unit([_MWH], [1])
        b = Unit([_MWH], [1])
        self.assertEqual(id(a), id(b))

    def test_numerator_and_denominator(self):
        test_unit = DAY * GBP / MWH
        self.assertEqual(test_unit.numerator, DAY * GBP)
        self.assertEqual(test_unit.denominator, MWH)


class QuantityTestCase(unittest.TestCase):

    def test_eq(self):
        self.assertEqual(50 * THERM, 50 * MWH_PER_THERM * MWH)
        nbp_in_therms = array([50, 60, 70], THERM)
        self.assertEqual(nbp_in_therms, Quantity(np.array([50, 60, 70]) * MWH_PER_THERM, MWH))
        self.assertNotEqual(nbp_in_therms, 50)
        self.assertEqual(array([0, 0, 0], GBP), 0)
        self.assertEqual(0, array([0, 0, 0], GBP))

    def test_conversion_within_unit_type(self):
        nbp_in_therms = 50 * THERM
        nbp_mwh = nbp_in_therms.convert(MWH)
        self.assertEqual(nbp_mwh.unit, MWH)
        self.assertEqual(nbp_mwh.value, 50 * MWH_PER_THERM)

    def test_reverse_conversion_within_unit_type(self):
        five_days = 5 * DAY
        hours = five_days.convert(HOUR)
        self.assertEqual(hours.value, 120)
        self.assertEqual(hours.unit, HOUR)
        self.assertEqual(five_days.value, 5)
        self.assertEqual(five_days.unit, DAY)

    def test_conversion_into_anything(self):
        nbp_in_therms = 50.0 * THERM
        with self.assertRaises(UnitError):
            nbp_in_therms.convert(1.0)

    def test_mmbtu_conversion(self):
        result = 2 * THERM + 2 * MMBTU
        self.assertEqual(result, 2.2 * MMBTU)

    def test_simple_add(self):
        nbp_price1 = Quantity(50, Unit("PENCE / THERM"))
        nbp_price2 = Quantity(51, Unit("PENCE / THERM"))
        self.assertEqual(nbp_price1 + nbp_price2, Quantity(101, Unit("PENCE / THERM")))

    def test_unit_add(self):
        nbp_price1 = Quantity(50, Unit("PENCE / THERM"))
        nbp_price2 = Quantity(20, Unit("GBP / MWH"))
        self.assertEqual(nbp_price1 + nbp_price2, Quantity(20 + 50 / MWH_PER_THERM * 0.01, Unit("GBP / MWH")))

    def test_unit_impossible_add(self):
        nbp_price = Quantity(50, Unit("PENCE / THERM"))
        oil_price = Quantity(10, Unit("USD / BBL"))
        with self.assertRaises(UnitError):
            nbp_price + oil_price
        with self.assertRaises(TypeError):
            nbp_price + 1
        with self.assertRaises(TypeError):
            1 + nbp_price

    def test_unit_subtraction(self):
        """ Since we're using += to implement + and -, we need to make sure it really
        is doing a deepcopy. Otherwise == changes the value. Only shows up on arrays, not floats"""
        nbp_price1 = Quantity(np.array([50]), Unit("PENCE / THERM"))
        nbp_price1_copy = Quantity(np.array([50]), Unit("PENCE / THERM"))
        nbp_price2 = Quantity(20, Unit("GBP / MWH"))
        nbp_price2_copy = Quantity(20, Unit("GBP / MWH"))
        self.assertEqual(nbp_price1 - nbp_price2,
                         Quantity(np.array([-20 + 50 / MWH_PER_THERM * 0.01]), Unit("GBP/MWH")))
        # check that subtraction hasn't changes the arguments
        self.assertEqual(nbp_price1, nbp_price1_copy)
        self.assertEqual(nbp_price2, nbp_price2_copy)

    def test_simple_division(self):
        price = Quantity(10, Unit("USD"))
        wti_price = Quantity(100, Unit("USD / BBL"))
        delta = price / wti_price
        self.assertEqual(delta, Quantity(0.1, BBL))
        efficiency = 0.5
        nbp_price = Quantity(50, Unit("PENCE/THERM"))
        power_cost = nbp_price / efficiency
        self.assertEqual(power_cost.convert(Unit("GBP / MWH")), Quantity(1 / MWH_PER_THERM, Unit("GBP / MWH")))
        self.assertEqual(nbp_price / 5, Quantity(10, Unit("PENCE / THERM")))
        self.assertEqual(1 / nbp_price, Quantity(1 / 50, Unit("PENCE / THERM").inverse))

    def test_nd_array_division(self):
        efficiency = 0.5
        nbp_price = array([50, 60, 70], Unit("PENCE / THERM"))
        power_cost = nbp_price / efficiency
        self.assertEqual(Quantity(2 * np.array([50, 60, 70]) / 100 / MWH_PER_THERM, Unit("GBP / MWH")), power_cost)
        price = array([10, 20], Unit("USD"))
        wti_price = 100 * Unit("USD / BBL")
        delta = price / wti_price
        self.assertEqual(Quantity(np.array([0.1, 0.2]), BBL), delta)

    def test_iterability(self):
        array_value = array([50, 60, 70], Unit("PENCE / THERM"))
        self.assertEqual(list(enumerate(array_value)),
                         [(0, Quantity(50, Unit("PENCE / THERM"))),
                          (1, Quantity(60, Unit("PENCE / THERM"))),
                          (2, Quantity(70, Unit("PENCE / THERM")))])

    def test_nd_array_functions(self):
        nbp_price = array([50, 60, -70], Unit("PENCE / THERM"))
        # get item
        self.assertEqual(nbp_price[1], Quantity(60, Unit("PENCE / THERM")))
        # __iter__
        self.assertEqual([x for x in nbp_price], [Quantity(x, Unit("PENCE / THERM")) for x in [50, 60, -70]])
        # abs
        self.assertEqual(abs(nbp_price), Quantity(np.array([50, 60, 70]), Unit("PENCE / THERM")))
        # len
        self.assertEqual(len(Quantity(np.array([50, 60, 70]), Unit("PENCE / THERM"))), 3)
        self.assertEqual(len(Quantity(np.array([40]), Unit("PENCE / THERM"))), 1)
        with self.assertRaises(TypeError):
            len(Quantity(1, Unit("PENCE / THERM")))

    def test_multiplication(self):
        a = 100 * GBP / MWH
        self.assertEqual(a * 1, a)
        self.assertEqual(1 * a, a)
        b = array([1, 2, 3], Unit("MWH / GBP")) * GBP
        self.assertEqual(b * 1, b)
        self.assertEqual(1 * b, b)

    def test_multiplication_conversion_factor(self):
        d = (1 * GBP) * (0.01 / PENCE)
        self.assertEqual(d, 1)

    def test_division_conversion_factor(self):
        c = 0.01 * GBP / (1 * PENCE)
        self.assertEqual(c, 1)

    def test_multiplication_by_unit(self):
        a = 100 * GBP * PENCE
        self.assertEqual(a, Quantity(1, GBP * GBP))

    def test_multiplication_by_quantities(self):
        a = 100 * GBP
        b = 10 * MWH
        self.assertEqual(a * b, 1000 * GBP * MWH)

    def test_multiply_unit_by_value(self):
        self.assertEqual(Quantity(50, Unit("PENCE / THERM")), 50 * PENCE / THERM)
        self.assertEqual(50 * GBP / MWH, Quantity(50, Unit("GBP / MWH")))
        self.assertEqual(50 / MWH * GBP, Quantity(50, Unit("GBP / MWH")))

    def test_multiply_unit_by_array_value(self):
        self.assertTrue(all(np.array([50 * GBP, 60 * GBP]) == np.array([50, 60]) * GBP))
        self.assertEqual(array([50, 60], GBP), GBP * np.array([50, 60]))
        self.assertEqual(array([50, 60], GBP), array([50, 60], Unit("GBP / BBL")) * BBL)

    def test_multipy_quantity_by_array_value(self):
        unitprice = 1000 * GBP
        self.assertTrue(all((np.array([50, 60]) * unitprice == np.array([Quantity(50000, GBP), Quantity(60000, GBP)]))))
        self.assertEqual(unitprice * np.array([50, 60]), Quantity([50000, 60000], GBP))
        self.assertEqual(array([50, 60], EUR) * unitprice, Quantity([50000, 60000], GBP * EUR))
    #
    # def test_mul_with_cf(self):
    #

a = np.array([1 * GBP])
print(a, type(a), a.dtype)
b = GBP * a
print(b,type(b))

gbp = _BaseUnit("gbp", 1)
pence = _DerivedUnit("pence", 0.01, gbp)
thousand = _DerivedUnit("thousand", 1000, gbp)
eur = _BaseUnit("eur", 1)
wti = _BaseUnit("wti", 1)
br = _BaseUnit("br", 1)
unit = Unit("wti/pence")
print(unit)
other_unit = 100
print((Unit([pence], [1]) * unit))
bob = Quantity("[100, 200] pence/wti")
print("bob", bob, bob.value, type(bob.value), len(bob.value))
print(Unit.standardise(Unit("thousand / wti"), Unit("pence / wti")))
james = Quantity("100 thousand/wti")
print(bob - james)
print(list(bobby ** -0.5 for bobby in bob))
print(bob)
bob[1] = Quantity("1000 * gbp/wti")
print(bob)
guillermo = Quantity("1 gbp / wti")
print(guillermo >= Quantity("1000 * pence/wti"))