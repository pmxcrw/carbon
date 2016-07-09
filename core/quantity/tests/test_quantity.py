from core.quantity.quantity import UnitError, _AbstractUnit, _BaseUnit, _DerivedUnit, Unit, Quantity, \
    _MWH, MWH, _THERM, THERM, DAY, HOUR, MW, _TONNE, TONNE, MMBTU, KWH, MTHERM, _BBL, BBL, \
    _PENCE, PENCE, _GBP, GBP, _EUR, EUR, _USD, USD, MWH_PER_THERM, DIMENSIONLESS, unique_unit, standardise, \
    mean, ones, array, amax, empty, reshape, concatenate, var, floor, ceil, arange, zeros, maximum, minimum

import numpy as np
import datetime as dt
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

    def test_parse(self):
        self.assertEqual(Unit("USD.GBP^2 / BBL^3.EUR"), Unit((_BBL, _USD, _GBP, _EUR), (-3, 1, 2, -1)))
        self.assertEqual(Unit("MWH/(BBL^2.TONNE^3)"), Unit((_MWH, _BBL, _TONNE), (1, -2, -3)))
        self.assertEqual(Unit("(MWH^2.TONNE) /(BBL^3)"), Unit((_MWH, _TONNE, _BBL), (2, 1, -3)))
        self.assertEqual(Unit("USD / USD"), DIMENSIONLESS)
        with self.assertRaises(ValueError):
            Unit("MWH/(BBL^2.TONNE^3")
        with self.assertRaises(ValueError):
            Unit("(MWH^3.TONNE/BBL)")
        self.assertEqual(Unit(""), DIMENSIONLESS)
        self.assertEqual(Unit(" "), DIMENSIONLESS)

    def test_standardise(self):
        lhs = Unit("PENCE / THERM")
        rhs = Unit("GBP / THERM")
        self.assertEqual(Unit.standardise(lhs, rhs), (Quantity(0.01, rhs), Quantity(1, rhs)))
        rhs = Unit("GBP / MWH")
        self.assertEqual(Unit.standardise(lhs, rhs), (Quantity(0.01 / MWH_PER_THERM, rhs), Quantity(1, rhs)))
        rhs = Unit("USD / BBL")
        self.assertEqual(Unit.standardise(lhs, rhs), (Quantity(1, lhs), Quantity(1, rhs)))
        rhs = DIMENSIONLESS
        self.assertEqual(Unit.standardise(lhs, rhs), (Quantity(1, lhs), Quantity(1, rhs)))

    def test_reference_unit(self):
        self.assertEqual(Unit("PENCE / THERM").reference_unit, Quantity(0.01 / MWH_PER_THERM, Unit("GBP / MWH")))
        self.assertEqual(DIMENSIONLESS.reference_unit, Quantity(1, DIMENSIONLESS))

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
        self.assertEqual(1 * GBP, GBP)
        self.assertEqual(GBP * 1, GBP)
        self.assertTrue(all(np.array([1, 2]) * GBP == np.array([1 * GBP, 2 * GBP])))
        self.assertEqual(GBP * np.array([1, 2]), Quantity(np.array([1, 2]), GBP))
        self.assertTrue(all(np.array([1 * GBP, 2 * GBP]) * GBP == np.array([1 * GBP * GBP, 2 * GBP * GBP])))
        self.assertTrue(all(GBP * np.array([1 * GBP, 2 * GBP]) == np.array([1 * GBP * GBP, 2 * GBP * GBP])))
        self.assertTrue(all(np.array([1 * GBP, 2 * GBP]) * GBP.inverse == np.array([1, 2])))
        self.assertTrue(all(GBP.inverse * np.array([1 * GBP, 2 * GBP]) == np.array([1, 2])))
        self.assertEqual(GBP * GBP.inverse, 1)
        self.assertEqual(THERM * THERM, Unit("THERM^2"))
        self.assertEqual(DIMENSIONLESS * THERM, THERM)
        self.assertEqual(THERM * DIMENSIONLESS, THERM)
        self.assertTrue(all(np.array([50 * GBP, 60 * GBP]) == np.array([50, 60]) * GBP))

    def test_divide(self):
        self.assertEqual(Unit("PENCE /THERM") / PENCE, Unit("1/THERM"))
        self.assertEqual(Unit("PENCE / THERM") / THERM, Unit("PENCE / THERM^2"))
        self.assertEqual(Unit("PENCE/THERM") / MWH, Quantity(1/MWH_PER_THERM, Unit("PENCE/MWH^2")))
        self.assertEqual(MWH / Unit("PENCE / THERM"), Quantity(MWH_PER_THERM, Unit("MWH^2/PENCE")))
        self.assertEqual(GBP / Unit("MWH / PENCE"), Quantity(0.01, Unit("GBP^2/MWH")))
        self.assertEqual(GBP / 100, Quantity(0.01, GBP))
        self.assertEqual(100 / GBP, Quantity(100, GBP.inverse))
        self.assertEqual(1 / GBP, GBP.inverse)
        self.assertEqual(GBP / 1, GBP)
        self.assertEqual(GBP / GBP, 1)
        self.assertTrue(all(np.array([1, 2]) / GBP == np.array([1 / GBP, 2 / GBP])))
        self.assertEqual(GBP / np.array([1, 2]), Quantity(np.array([1, 0.5]), GBP))
        self.assertTrue(all(np.array([1 * GBP, 2 * GBP]) / GBP == np.array([1, 2])))
        self.assertTrue(all(GBP / np.array([1 * GBP, 2 * GBP]) == np.array([1, 0.5])))
        self.assertTrue(all(np.array([1 * GBP, 2 * GBP]) / BBL == np.array([1 * GBP / BBL, 2 * GBP / BBL])))
        self.assertTrue(all(GBP / np.array([1 * BBL, 2 * BBL]) == np.array([1 * GBP / BBL, 0.5 * GBP / BBL])))
        self.assertEqual(Quantity(10, GBP) / Unit("PENCE / THERM"), Quantity(1000, THERM))
        self.assertEqual(Unit("PENCE / THERM") / Quantity(10, GBP), Quantity(0.001, Unit("1/THERM")))
        self.assertEqual(Unit("PENCE")/Unit("THERM"), Unit("PENCE/THERM"))
        self.assertEqual(Unit("PENCE") / Unit("GBP"), 0.01)
        a = 1 / DAY
        self.assertEqual(type(a), type(1 * DAY))
        self.assertEqual(1 / a, 1 * DAY)
        self.assertEqual(DIMENSIONLESS / THERM, THERM.inverse)
        self.assertEqual(THERM / DIMENSIONLESS, THERM)

    def test_inverse(self):
        self.assertEqual(Unit("PENCE/THERM"), Unit("THERM/PENCE").inverse)
        self.assertEqual(DIMENSIONLESS.inverse, DIMENSIONLESS)

    def test_equals(self):
        self.assertEqual(Unit("PENCE/THERM"), Unit((_THERM, _PENCE), (-1, 1)))
        self.assertEqual(Unit((_THERM, _PENCE), (-1, 1)), Unit((_PENCE, _THERM), (1, -1)))

    def test_str(self):
        self.assertEqual(str(Unit((_THERM, _PENCE), (-1, 1))), "PENCE / THERM")
        self.assertEqual(str(Unit((_THERM, _PENCE, _BBL), (-1, 1, -2))), "PENCE / (BBL^2.THERM)")
        self.assertEqual(str(Unit((_THERM, _PENCE), (-2, 4))), "PENCE^4 / THERM^2")
        self.assertEqual(str(Unit([_THERM], [-1])), "1 / THERM")
        self.assertEqual(str(DIMENSIONLESS), "DIMENSIONLESS")

    def test_conversion_factor(self):
        self.assertEqual(MWH_PER_THERM, THERM.conversion_factor(MWH))
        with self.assertRaises(UnitError):
            MWH.conversion_factor(BBL)
        self.assertEqual(1 / 1000, KWH.conversion_factor(MWH))
        self.assertEqual(1e6, MTHERM.conversion_factor(THERM))
        with self.assertRaises(UnitError):
            DIMENSIONLESS.conversion_factor(BBL)
        with self.assertRaises(UnitError):
            BBL.conversion_factor(DIMENSIONLESS)

    def test_equivalent(self):
        self.assertTrue(THERM.equivalent(MWH))
        self.assertTrue(MWH.equivalent(THERM))
        self.assertFalse(MWH.equivalent(BBL))
        self.assertFalse(DIMENSIONLESS.equivalent(BBL))
        self.assertFalse(BBL.equivalent(DIMENSIONLESS))

    def test_name(self):
        ppt = PENCE / THERM
        self.assertEqual(ppt.name, "PENCE / THERM")
        self.assertEqual(DIMENSIONLESS.name, "DIMENSIONLESS")

    def test_unit_identity(self):
        a = Unit([_MWH], [1])
        b = Unit([_MWH], [1])
        self.assertEqual(id(a), id(b))

    def test_numerator_and_denominator(self):
        test_unit = DAY * GBP / MWH
        self.assertEqual(test_unit.numerator, DAY * GBP)
        self.assertEqual(test_unit.denominator, MWH)
        self.assertEqual(DIMENSIONLESS.numerator, DIMENSIONLESS)
        self.assertEqual(DIMENSIONLESS.denominator, DIMENSIONLESS)
        test_unit = GBP
        self.assertEqual(test_unit.numerator, GBP)
        self.assertEqual(test_unit.denominator, DIMENSIONLESS)


class QuantityTestCase(unittest.TestCase):

    def test_eq(self):
        self.assertEqual(50 * THERM, 50 * MWH_PER_THERM * MWH)
        nbp_in_therms = Quantity([50, 60, 70], THERM)
        self.assertEqual(nbp_in_therms, Quantity(np.array([50, 60, 70]) * MWH_PER_THERM, MWH))
        self.assertNotEqual(nbp_in_therms, 50)
        self.assertEqual(Quantity([0, 0, 0], GBP), 0)
        self.assertEqual(0, Quantity([0, 0, 0], GBP))
        self.assertEqual(array([0, 0, 0]), 0)
        self.assertEqual(0, array([0, 0, 0]))

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
        nbp_price = Quantity([50, 60, 70], Unit("PENCE / THERM"))
        power_cost = nbp_price / efficiency
        self.assertEqual(Quantity(2 * np.array([50, 60, 70]) / 100 / MWH_PER_THERM, Unit("GBP / MWH")), power_cost)
        price = Quantity([10, 20], Unit("USD"))
        wti_price = 100 * Unit("USD / BBL")
        delta = price / wti_price
        self.assertEqual(Quantity(np.array([0.1, 0.2]), BBL), delta)

    def test_iterability(self):
        array_value = Quantity([50, 60, 70], Unit("PENCE / THERM"))
        self.assertEqual(list(enumerate(array_value)),
                         [(0, Quantity(50, Unit("PENCE / THERM"))),
                          (1, Quantity(60, Unit("PENCE / THERM"))),
                          (2, Quantity(70, Unit("PENCE / THERM")))])

    def test_nd_array_functions(self):
        nbp_price = Quantity([50, 60, -70], Unit("PENCE / THERM"))
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
        b = Quantity([1, 2, 3], Unit("MWH / GBP")) * GBP
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
        self.assertEqual(Quantity([50, 60], GBP), GBP * array([50, 60]))
        self.assertEqual(Quantity([50, 60], GBP), array([50, 60]) * GBP)

    def test_multipy_quantity_by_array_value(self):
        unitprice = 1000 * GBP
        self.assertTrue(all((np.array([50, 60]) * unitprice == np.array([Quantity(50000, GBP), Quantity(60000, GBP)]))))
        self.assertEqual(unitprice * np.array([50, 60]), Quantity([50000, 60000], GBP))
        self.assertEqual(array([50, 60]) * unitprice, Quantity([50000, 60000], GBP))
        self.assertEqual(unitprice * array([50, 60]), Quantity([50000, 60000], GBP))
        self.assertEqual(type(unitprice * array([50, 60])), type(array([50, 60]) * unitprice))

    def test_mul_with_cf(self):
        q1a = 1 * MW
        q1b = 1 * MW * (24 * HOUR / DAY)
        q1c = 1 * MW * 24 * HOUR / DAY
        self.assertEqual(q1b, q1c)
        self.assertEqual(q1a, q1b)
        self.assertEqual(q1c, q1a)

        # check multiplication by quantity without decay but with conversion factor
        q2 = Quantity(np.array([2.0]), DAY * GBP / MWH)
        self.assertEqual(q1a * q2, q1b * q2)
        self.assertEqual(q1a * q2, q1c * q2)

        # check multiplication by quantity with decat and conversion factor
        q3 = MWH / DAY * np.array([4])
        q4 = HOUR / MWH * np.array([5])
        self.assertEqual((q3 * q4).unit, DIMENSIONLESS)
        self.assertAlmostEqual(float((q3 * q4).value), 20/24)

    def test_div_with_cf(self):
        q1a = 1 * MW
        q1b = (1 * MW * 24 * HOUR) / DAY
        self.assertEqual(q1a, q1b)

        # check division by quantity without decay but with conversion factor
        q2 = Quantity(np.ndarray([2.0]), DAY * GBP / MWH)
        self.assertEqual(q1a / q2, q1b / q2)

        # check division by quantity with decay and conversion factor
        q3 = MWH / DAY * np.array([4])
        q4 = MWH / HOUR * np.array([5])
        self.assertEqual((q3 / q4).unit, DIMENSIONLESS)
        self.assertAlmostEqual(float((q3 / q4).value), 1 / 24 * 4 / 5)

    def test_sum_quantity(self):
        q1 = 1 * THERM
        q2 = 2 * THERM
        q3 = 3 * MWH
        q4 = 4 * BBL
        list_convertible_quantity = [q1, q2, q3]
        self.assertEqual(sum(list_convertible_quantity), q1 + q2 + q3)
        self.assertEqual(sum(list_convertible_quantity), (3 * MWH_PER_THERM + 3) * MWH)
        with self.assertRaises(UnitError):
            sum([q1, q2, q4])

    def test_sum_array(self):
        self.assertEqual(sum([Quantity([1, 2], MWH), Quantity([3, 4], MWH)]), Quantity([4, 6], MWH))
        self.assertEqual(sum([array([1, 2], MWH), array([3, 4], MWH)]), array([4, 6], MWH))

    def test_array_broadcasting(self):
        self.assertEqual(sum([1 * MWH, Quantity([3, 4], MWH)]), Quantity([4, 5], MWH))
        self.assertEqual(sum([Quantity([3, 4], MWH), 1 * MWH]), Quantity([4, 5], MWH))

    def test_round(self):
        self.assertEqual((1.23456 * THERM).round(2), 1.23 * THERM)
        self.assertEqual((1.23456 * THERM).round(3), 1.235 * THERM)
        self.assertEqual((Quantity([1.23456, 2.34567], THERM)).round(3), array([1.235, 2.346], THERM))

    def test_units_decay_to_floats(self):
        q1 = 1 * THERM
        q2 = 2 * THERM
        res = q1 / q2
        self.assertEqual(res, 0.5)
        self.assertTrue(isinstance(res, float))
        q3 = 2 / THERM
        res = q1 * q3
        self.assertEqual(res, 2.0)
        self.assertTrue(isinstance(res, float))

    def test_multi_unit_arithemetic(self):
        lhs = (GBP / MWH)
        rhs = (PENCE / THERM)
        expected_factor = 100 * MWH_PER_THERM
        self.assertEqual(lhs / rhs, expected_factor)
        self.assertEqual(GBP / MWH / PENCE / THERM, (100 / MWH_PER_THERM) / MWH / MWH)
        scale_factor = (GBP / MWH) / (PENCE / THERM)
        self.assertEqual(scale_factor, expected_factor)
        scale_factor = 1 * (GBP / MWH) / (PENCE / THERM)
        self.assertEqual(scale_factor, expected_factor)

    def test_division_again(self):
        simulated_nbp = 1 * PENCE / THERM
        expected_nbp = 1 * PENCE / THERM
        df = 0.99
        expected_delta = 1 * df * (simulated_nbp / expected_nbp)
        self.assertTrue(isinstance(expected_delta, float))

        # DAY / DAY should decat to float, but that shouldn't matter for comparison
        self.assertEqual(Quantity(0, DAY) / Quantity(0.5, DAY), Quantity(0))
        self.assertEqual(Quantity(0, DAY) / Quantity(0.5, DAY), 0)
        # check non zero case too, because zero gets special treatment
        self.assertEqual(Quantity(1, DAY) / Quantity(0.5, DAY), Quantity(2))
        self.assertEqual(Quantity(1, DAY) / Quantity(0.5, DAY), 2)

    def test_zero_multiplication(self):
        one_therm = 1 * THERM
        one_gbp = 1 * GBP
        self.assertEqual(0 * one_therm, 0 * THERM)
        self.assertEqual(one_therm * 0, 0 * THERM)
        self.assertEqual(0 * one_therm, 0)
        self.assertEqual(one_therm * 0, 0)
        self.assertNotEqual(0 * one_therm, 0 * one_gbp)

    def test_zero_addition(self):
        one_therm = 1 * THERM
        one_gbp = 1 * GBP
        self.assertEqual(0 + one_therm, one_therm)
        self.assertEqual(one_therm + 0, one_therm)
        self.assertNotEqual(0 + one_therm, 0 + one_gbp)

    def test_zero_addition_array(self):
        one_therm = 1 * THERM
        one_therm_array = ones(2, THERM)
        zero_array = np.zeros(2)
        self.assertEqual(one_therm_array + zero_array, one_therm_array)
        self.assertTrue(all(zero_array + one_therm_array == one_therm_array))

        # check we preserve shapes
        self.assertTrue(all(zero_array + one_therm == one_therm_array))
        self.assertEqual(one_therm + zero_array, one_therm_array)

        # check that incompatible shapes don't work
        with self.assertRaises(ValueError):
            ones(2, THERM) + np.zeros(3)
        with self.assertRaises(ValueError):
            ones(3, THERM) + np.zeros(2)
        with self.assertRaises(ValueError):
            np.zeros(3) + ones(2, THERM)
        with self.assertRaises(ValueError):
            np.zeros(2) + ones(3, THERM)

    def test_equality_with_units(self):
        self.assertEqual(1 * THERM, THERM)

    def test_zero_subtraction_and_equality_to_zero(self):
        one_therm = 1 * THERM
        one_gbp = 1 * GBP
        self.assertEqual(0 - one_therm, -one_therm)
        self.assertEqual(one_therm - 0, one_therm)
        self.assertEqual(one_therm - one_therm, 0)
        self.assertNotEqual(0 - one_therm, 0 - one_gbp)
        self.assertNotEqual(one_therm - one_therm, one_gbp - one_gbp)
        self.assertEqual(one_therm - one_therm, 0)
        self.assertEqual(0, one_gbp - one_gbp)

    def test_equality_to_zero(self):
        self.assertTrue(0 == 0 * THERM)
        self.assertTrue(0 * GBP == 0)
        self.assertTrue(0.0 * GBP == 0 * DIMENSIONLESS)
        self.assertTrue(0 * DIMENSIONLESS == 0.0 * GBP)
        self.assertTrue(zeros(3, GBP) == zeros(3, DIMENSIONLESS))
        self.assertTrue(0 == zeros(3, GBP))
        self.assertTrue(0 == zeros(3, DIMENSIONLESS))
        self.assertEqual(zeros(3, GBP), zeros(3, DIMENSIONLESS))

    def test_non_equality_to_nonzero(self):
        self.assertNotEqual(1, 1 * GBP)
        self.assertNotEqual(2 * GBP, 2)
        self.assertNotEqual(3.0 * GBP, 3 * DIMENSIONLESS)
        self.assertNotEqual(3 * DIMENSIONLESS, 4 * GBP)
        self.assertEqual([], 0 * GBP)  # TODO is this right? Thorn tests that this is not equal

    def test_zero_stays_united(self):
        one_therm = 1 * THERM
        one_gbp = 1 * GBP
        with self.assertRaises(UnitError):
            one_therm - one_therm + one_gbp
        with self.assertRaises(UnitError):
            (one_therm - one_therm) + one_gbp
        with self.assertRaises(UnitError):
            one_therm - (one_therm + one_gbp)

    def test_nonzero(self):
        self.assertTrue(1 * THERM)
        self.assertFalse(0 * THERM)

    def test_numpy_array_length_1_behaviour(self):
        np_arr = np.ones(1)
        some_int = 5
        some_np_arr = some_int * np_arr

        q_arr = Quantity(np.ones(1), DIMENSIONLESS)
        some_q = Quantity(5, DIMENSIONLESS)
        some_q_arr = some_q * q_arr

        self.assertEqual(some_int, some_np_arr)
        self.assertEqual(some_q, some_q_arr)

    def test_inverse_of_unit_gives_unit(self):
        a = GBP
        self.assertEqual(a.inverse, (1 / a).unit)
        self.assertTrue(isinstance(a, Unit))

    def test_arrays_dont_decay_mul(self):
        a = Quantity([1.0], GBP)
        inv = 1 / GBP
        actual = a * inv
        self.assertEqual(actual, Quantity([1.0], DIMENSIONLESS))
        b = 1 / GBP * array([1])
        self.assertEqual(b * GBP, array([1]))

    def test_arrays_dont_decay_div(self):
        a = array([1], GBP)
        self.assertEqual(a / GBP, array([1], DIMENSIONLESS))
        b = Quantity(1, GBP)
        self.assertEqual(a / b, array([1], DIMENSIONLESS))
        c = array([1], GBP)
        self.assertEqual(a / c, array([1], DIMENSIONLESS))

    def test_compare(self):
        a = array([3, 6, 9], GBP)
        b = array([1, 6, 10], GBP)
        c = array([1, 6, 10], EUR)
        c = a > b
        d = a < b
        e = a > 0
        f = a < 0
        self.assertTrue(np.all(c == np.array([True, False, False])))
        self.assertFalse(a == b)
        self.assertTrue(np.all(d == np.array([False, False, True])))
        self.assertTrue(np.all(e == np.array([True, True, True])))
        self.assertTrue(np.all(f == np.array([False, False, False])))
        with self.assertRaises(TypeError):
            a < c
        with self.assertRaises(TypeError):
            a < 45

    def test_complex_compare(self):
        a = array([3, 6, 9], GBP)
        b = array([100, 600, 1000], PENCE)
        c = a > b
        d = a == b
        e = a < b
        self.assertTrue(np.all(c == np.array([True, False, False])))
        self.assertTrue(np.all(d == np.array([False, False, False])))
        self.assertTrue(np.all(e == np.array([False, False, True])))

    def test_numpy_array_overrides(self):
        a = array([3, -6, 9], GBP)
        self.assertEqual(Quantity(2, GBP), mean(a))
        self.assertEqual(array([1, 1, 1], GBP), ones(3, GBP))
        self.assertEqual(Quantity(9, GBP), amax(a))
        self.assertEqual(amax.__name__, 'amax')

    def test_numpy_floats(self):
        a = np.float64(71.111)
        self.assertEqual(a * (1.0 * DAY), Quantity(71.111, DAY))

    def test_addition_between_scalars_and_SCALAR(self):
        self.assertEqual(1 + Quantity(0.03, DIMENSIONLESS), 1.03)
        self.assertEqual(Quantity(0.03, DIMENSIONLESS) + 1, 1.03)
        self.assertTrue(all(np.array([1,1]) + Quantity(0.03, DIMENSIONLESS) == np.array([1.03, 1.03])))
        self.assertTrue(all(Quantity(0.03, DIMENSIONLESS) + np.array([1, 1]) == np.array([1.03, 1.03])))

    def test_argmax(self):
        a = Quantity(np.array([1, 4, 2, 7, 1]), GBP)
        self.assertEqual(a.argmax(), 3)

    def test_max_in_list_of_quantities(self):
        quantity_list = [Quantity(5, GBP), Quantity(2, GBP)]
        self.assertEqual(Quantity(5, GBP), max(quantity_list))
        quantity_list_diff_units = [Quantity(5, GBP), Quantity(2, USD)]
        with self.assertRaises(UnitError):
            max(quantity_list_diff_units)

    def test_minimum_maximum(self):
        a = Quantity([1, 4, 2, 7, 1], GBP)
        b = Quantity([1, 5, 1, 1, 5], GBP)
        self.assertEqual(maximum(a, b), array([1, 5, 2, 7, 5], GBP))
        self.assertEqual(minimum(a, b), array([1, 4, 1, 1, 1], GBP))
        d = Quantity(np.array([1, 5, 1, 1, 5]), USD)
        with self.assertRaises(UnitError):
            maximum(a, d)
        with self.assertRaises(UnitError):
            minimum(a, d)

    def test_increment_add_identity(self):
        q = Quantity(1, GBP)
        ls = []
        ls.append(q)
        q += 2 * GBP
        self.assertEqual(ls[0], 1 * GBP)

    def test_increment_add_sanity(self):
        ''' checks that a +=b gives the same result as a = a + b'''
        sum1 = 0
        list1= []
        sum2 = 0
        list2 = []
        values = range(5)
        for i in values:
            payoff = Quantity(i, GBP)
            sum1 += payoff
            list1.append(sum1)
            sum2 = sum2 + payoff
            list2.append(sum2)
        self.assertEqual(sum1, sum(values) * GBP)
        self.assertEqual(sum1, sum2)
        self.assertEqual(list1, list2)
        for i in range(len(values)):
            self.assertEqual(list1[i], sum(values[:i + 1]) * GBP)

    def test_mutable_array(self):
        n_decisions = 3
        n_path = 4
        full_continuation_values = empty((n_decisions, n_path))
        temp = []
        for i in range(n_decisions):
            immediate_payoff = ones(n_path) * GBP
            continuation_value = array([i] * n_path) * GBP
            full_continuation_values[i, :] = immediate_payoff + continuation_value
            temp.append(immediate_payoff + continuation_value)
        expected = reshape(concatenate(temp), (n_decisions, n_path))
        self.assertEqual(expected, full_continuation_values)

    def test_mutable_array_float_assignment(self):
        mutable_array = empty((2, 2))
        initial_unit = mutable_array.unit
        mutable_array[1, 1] = 1

    def test_mutable_array_units(self):
        gbp_quantity_arr = ones(3, GBP)
        with self.assertRaises(UnitError):
            gbp_quantity_arr[1] = 1 * EUR

    def test_var(self):
        sample = np.array([1, 2, 3])
        quantity_sample = GBP * sample
        sample_var = np.var(sample)
        quantity_sample_var = var(quantity_sample)
        self.assertEqual(quantity_sample_var, sample_var * GBP * GBP)

    def test_unit_adoption_null_quantity(self):
        no_unit = 0 * DIMENSIONLESS
        has_unit = 1 * THERM
        self.assertEqual(no_unit + has_unit, 1 * THERM)
        self.assertEqual(has_unit + no_unit, 1 * THERM)

    def test_unit_adoption(self):
        no_unit = Quantity(0)
        has_unit = 1 * THERM
        self.assertEqual(no_unit + has_unit, 1 * THERM)
        self.assertEqual(has_unit + no_unit, 1 * THERM)

    def test_inf_quantity_equality(self):
        n = Quantity(np.inf, THERM)
        self.assertEqual(n, n)

    def test_divide_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            Quantity(1, GBP) / 0
        with self.assertRaises(ZeroDivisionError):
            Quantity(1, GBP) / np.zeros(2)
        with self.assertRaises(ZeroDivisionError):
            ones(2, GBP) / 0.0
        with self.assertRaises(ZeroDivisionError):
            ones(2, GBP) / np.zeros(2)

    def test_unit_unicity(self):
        a = GBP / THERM * np.array([1, 2, 3, 4])
        b = GBP / THERM * np.array([5, 6, 7, 8])
        #self.assertTrue(a[0].unit is a[1].unit)
        self.assertTrue(a[0].unit is a.unit)
        self.assertTrue(a[0].unit is b[0].unit)
        self.assertTrue(a[0].unit is b.unit)

    def test_mean(self):
        a = Quantity([1, 2, 3], GBP)
        self.assertEqual(mean(a), GBP * 2)
        self.assertEqual(array([1, 2, 3,], GBP).mean(), 2 * GBP)
        self.assertEqual((2 * GBP).mean(), 2 * GBP)

    def test_less_than(self):
        self.assertTrue(Quantity(5, THERM) < Quantity(10.0, THERM))
        self.assertTrue(Quantity(5,) < 10.0)
        with self.assertRaises(TypeError):
            Quantity(5, THERM) < 10.0

    def test_less_than_or_equal(self):
        self.assertTrue(Quantity(5, THERM) <= Quantity(10.0, THERM))
        self.assertTrue(THERM * 0 <= 0)
        self.assertFalse(THERM * 1 <= 0)
        self.assertTrue(THERM * -1 <= 0)
        self.assertTrue(Quantity(5,) <= 5.0)
        with self.assertRaises(TypeError):
            Quantity(5, THERM) <= 10

    def test_greater_than_or_equal(self):
        self.assertTrue(Quantity(10, THERM) >= Quantity(10, THERM))
        self.assertTrue(Quantity(11, THERM) >= Quantity(10, THERM))
        self.assertTrue(Quantity(5,) >= 5)
        with self.assertRaises(TypeError):
            Quantity(5, THERM) >= 10

    def test_equality_across_major_and_minor_units(self):
        self.assertEqual(Quantity(0.0166, GBP), Quantity(1.66, PENCE))

    def test_parse(self):
        test_cases = [(["Quantity(1.23, GBP/THERM)",
                        "1.23 GBP/THERM",
                        "1.23 * GBP/THERM"],
                        Quantity(1.23, GBP / THERM)),
                      (["Quantity([1.23, 4.56], GBP/THERM)",
                        "[1.23, 4.56] GBP/THERM",
                        "[1.23, 4.56] * GBP/THERM"],
                        Quantity([1.23, 4.56], GBP / THERM)),
                      (["Quantity(0.0, DIMENSIONLESS)",
                        "0.0",
                        "0.0 * "],
                        Quantity(0, DIMENSIONLESS)),
                      (["Quantity(1.0, MWH/(MWH.DAY))"],
                       Quantity(1.0, MWH / (MWH * DAY)))]
        for strings, expected_value in test_cases:
            for string in strings:
                self.assertEqual(Quantity(string), expected_value)

    def test_parse_failure(self):
        expected_failures = ["Quantity 1.23, GBP/THERM)",
                             "Quantity(1.23, GBP/THERM",
                             "Quantity(1.23, GBP/)"]
        for string in expected_failures:
            with self.assertRaises(ValueError):
                Quantity(string)

    def test_parse_roundtrip(self):
        test_cases = [Quantity(62.913, PENCE / THERM),
                      array([1, 2, 3], GBP),
                      Quantity([1.2, 7.78], EUR / MWH)]
        for quantity in test_cases:
            self.assertEqual(Quantity(str(quantity)), quantity)

    def test_set_item(self):
        qty = Quantity([0, 0, 0], DIMENSIONLESS)
        self.assertEqual(qty.unit, DIMENSIONLESS)
        qty[0] = THERM * 1
        self.assertEqual(qty.unit, THERM)
        qty[1] = THERM * 2
        self.assertEqual(qty, Quantity([1, 2, 0], THERM))
        with self.assertRaises(UnitError):
            qty[1] = 4
        with self.assertRaises(UnitError):
            qty[2] = BBL * 2

    def test_numpy_float64_expression(self):
        a = Quantity(np.float64(1.0), THERM) / Quantity(np.float64(1.0), THERM)
        self.assertTrue(a == 1.0)
        self.assertTrue(type(a) == np.float64)
        a = Quantity(np.float64(1), THERM)
        b = Quantity(np.float64(1), THERM)
        c = GBP
        d = PENCE / THERM
        f = a / b * c
        self.assertEqual(f, 1 * GBP)
        e = a / b * c / d
        self.assertEqual(e, 100 * THERM)
        self.assertEqual(a / b * c / d, (a * c) / (b * d))
        self.assertEqual(a / b * c / d, (a / b * c) / d)

    def test_pow(self):
        for x in [3 * GBP, 20 * PENCE, 2 * PENCE / THERM]:
            self.assertEqual(x ** 0, 1.0)
            self.assertEqual(pow(x, 0), 1)
            self.assertEqual(pow(x, 2), x * x)
            self.assertEqual(pow(x, 3), x * x * x)
            self.assertEqual(x ** 3, x * x * x)
            with self.assertRaises(TypeError):
                pow(x, x)

    def test_relational_operators(self):
        self.assertTrue(1 * GBP > 0)
        self.assertTrue(1 * GBP >= 0)
        self.assertTrue(1 * GBP != 0)

class FreeStandingQuantityFunctionsTestCase(unittest.TestCase):

    def test_standardise(self):
        self.assertEqual(standardise([1 * GBP, 12 * GBP]), [1 * GBP, 12 * GBP])
        self.assertEqual(standardise((Quantity([1, 2, 3], GBP), Quantity([100, 200, 300], PENCE))),
                         (Quantity([1, 2, 3], GBP), Quantity([1, 2, 3], GBP)))
        self.assertEqual(standardise({'a': Quantity(1, GBP), 'b': Quantity(2, GBP)}),
                         {'a': Quantity(1, GBP), 'b': Quantity(2, GBP)})
        test_dict = {100: Quantity(1, GBP), 200: Quantity(200, PENCE)}
        self.assertEqual(standardise(test_dict), {100: Quantity(1, GBP), 200: Quantity(2, GBP)})
        test_dict = {"feel": Quantity([1, 2, 3], PENCE / THERM), "good": Quantity([2.2, 3.4], GBP / MWH)}
        self.assertEqual(standardise(test_dict),
                         {"feel": Quantity([0.01 / MWH_PER_THERM,
                                            0.02 / MWH_PER_THERM,
                                            0.03 / MWH_PER_THERM], GBP / MWH),
                          "good": Quantity([2.2, 3.4], GBP / MWH)})
        standard = standardise(test_dict, PENCE / THERM)
        expected_values = [Quantity([1, 2, 3], PENCE / THERM),
                           Quantity([220 * MWH_PER_THERM, 340 * MWH_PER_THERM], PENCE / THERM)]
        self.assertTrue(np.all(abs(standard["feel"] - Quantity([1, 2, 3], PENCE / THERM)) < 1e-10 * PENCE / THERM))
        self.assertTrue(np.all(abs(standard["good"] - Quantity([220 * MWH_PER_THERM,
                                                                340 * MWH_PER_THERM],
                                                               PENCE / THERM)) < 1e-10 * PENCE / THERM))
        with self.assertRaises(UnitError):
            standardise([1 * GBP, 1 * MWH])
        with self.assertRaises(ValueError):
            standardise("cats")
        with self.assertRaises(ValueError):
            standardise(1 * PENCE / THERM)
        with self.assertRaises(UnitError):
            standardise([100 * PENCE, 1 * GBP], MWH)



    def test_concatenate(self):
        a = GBP * 1
        self.assertEqual(concatenate((a, GBP * 2, GBP * 3)), array((1, 2, 3), GBP))
        self.assertTrue(a.value.ndim == 0)
        self.assertEqual(concatenate((Quantity([1, 2, 3], GBP),Quantity([3, 4], GBP))),
                         Quantity([1, 2, 3, 3, 4], GBP))
        self.assertEqual(concatenate((Quantity([1, 2, 3], GBP), Quantity([1], GBP))), Quantity([1, 2, 3, 1], GBP))

    def test_concatenate_with_fungable_units(self):
        self.assertEqual(concatenate((THERM * 1 / MWH_PER_THERM, MWH * 1)), array((1, 1), MWH))
        self.assertEqual(concatenate((THERM * 1 / MWH_PER_THERM,
                                      THERM * 2 / MWH_PER_THERM,
                                      MWH * 1)), array((1, 2, 1), MWH))
        self.assertEqual(concatenate((Quantity([1, 2, 3], GBP),
                                      Quantity([300, 400, 500], PENCE),
                                      Quantity([6], GBP))), Quantity([1, 2, 3, 3, 4, 5, 6], GBP))

    def test_zeros(self):
        three = zeros(3, GBP)
        self.assertEqual(three, array([0, 0, 0], GBP))
        self.assertEqual(three.shape, (3,))
        mat = zeros((2, 2,), GBP)
        self.assertEqual(mat, array([[0, 0], [0, 0]], GBP))
        self.assertEqual(mat.shape, (2, 2))

    def test_floor_and_ceil(self):
        self.assertEqual(floor(1.1 * THERM), 1 * THERM)
        self.assertEqual(ceil(1.1 * THERM), 2 * THERM)
        self.assertEqual(floor(array([1.1, 2.2], THERM)), array([1, 2], THERM))

    def test_arange(self):
        expected = Quantity(np.arange(0.1, 10.1, 1.1), THERM)
        self.assertEqual(arange(0.1 * THERM, 10.1 * THERM, 1.1 * THERM), expected)

    def test_unique_units(self):
        scalar_quotes = {dt.date(2014, 1, 1): 1.25,
                         dt.date(2014, 4, 1): 1.26}
        self.assertEqual(unique_unit(scalar_quotes.values()), DIMENSIONLESS)
        consistent_quotes = {dt.date(2014, 1, 1): 1.25 * PENCE,
                             dt.date(2014, 4, 1): 1.26 * PENCE}
        self.assertEqual(unique_unit(consistent_quotes.values()), PENCE)
        inconsistent_quotes = {dt.date(2014, 1, 1): 1.25 * PENCE,
                               dt.date(2014, 4, 1): 1.26 * THERM}
        with self.assertRaises(UnitError):
            unique_unit(inconsistent_quotes.values())
