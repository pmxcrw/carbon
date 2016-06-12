from core.quantity.quantity import Unit, _AbstractUnit, _BaseUnit, _DerivedUnit, UnitError

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
        self.assertNotEqual(self.xyz, _AbstractUnit('pence', 100))

    def test_lt(self):
        self.assertLess(self.xyz, self.zyx)

class TestBaseUnits(unittest.TestCase):

    def setUp(self):
        self.usd = _BaseUnit('usd', 1)

    def test_new(self):
        self.assertEqual(self.usd.name, 'usd')
        self.assertEqual(self.usd.base_multiplier, 1)
        with self.assertRaises(AssertionError):
            _BaseUnit('pence', 100)

    def test_reference_unit(self):
        self.assertEqual(self.usd.reference_unit, self.usd)


class TestDerivedUnits(unittest.TestCase):

    def setUp(self):
        self.usd = _BaseUnit('usd', 1)
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
        self.usd = _BaseUnit('usd', 1)
        self.cents = _DerivedUnit('cents', 100, 'usd')
        self.cad = _BaseUnit('cad', 1)
        self.cad_cents = _DerivedUnit('cad_cents', 100, self.cad)
        self.eur = _BaseUnit('eur', 1)
        self.gbp = _BaseUnit('gbp', 1)
        self.pence = _DerivedUnit('pence', 100, 'gbp')
        self.jpy = _BaseUnit('jpy', 1)
        self.aud = _BaseUnit('aud', 1)

    def test_degeneracy(self):
        with self.assertRaises(UnitError):
            Unit([self.usd, self.gbp, self.cents], [1, 2, -1])

    def test_no_repeats(self):
        unit = Unit([self.usd, self.pence, self.cad, self.eur], [1, 1, -1, 2])
        self.assertEqual(unit.units, (self.cad, self.eur, self.pence, self.usd))
        self.assertEqual(unit.exponents, (-1, 2, 1, 1))

    def test_no_repeats_with_zeros(self):
        unit = Unit([self.jpy, self.pence, self.cad, self.eur, self.cents], [1, 1, -1, 0, 2])
        self.assertEqual(unit.units, (self.cad, self.cents, self.jpy, self.pence))
        self.assertEqual(unit.exponents, (-1, 2, 1, 1))

    def test_repeats_no_zeros(self):
        unit = Unit([self.cad, self.jpy, self.pence, self.cad, self.pence], [1, 1, 1, 1, 3])
        self.assertEqual(unit.units, (self.cad, self.jpy, self.pence))
        self.assertEqual(unit.exponents, (2, 1, 4))

    def test_repeats_easy_zero(self):
        unit = Unit([self.cad, self.aud, self.jpy, self.pence, self.cad, self.pence], [1, 0, 1, 1, 1, 3])
        self.assertEqual(unit.units, (self.cad, self.jpy, self.pence))
        self.assertEqual(unit.exponents, (2, 1, 4))

    def test_repeats_cancelling_unit(self):
        unit = Unit([self.cad, self.aud, self.jpy, self.pence, self.cad, self.pence], [1, 0, 1, 1, -1, 3])
        self.assertEqual(unit.units, (self.jpy, self.pence))
        self.assertEqual(unit.exponents, (1, 4))