from core.time_period.load_shape import LoadShape, BASE, PEAK, OFFPEAK, WEEKDAY,\
    WEEKDAY_OFFPEAK, WEEKEND, WEEKEND_PEAK, WEEKEND_OFFPEAK, DAYTIME, NIGHTTIME, \
    EXTENDED_DAYTIME, EXTENDED_PEAK, WEEKEND_EXTENDED_PEAK, NEVER_LS, HOURS,  EFAS, \
    WEEKDAY_EFAS, WEEKEND_EFAS

import unittest


class LoadShapeTests(unittest.TestCase):

    def test_create_bitmap(self):
        base = bin(LoadShape.create_bitmap(0, 24, True, True))
        weekday = bin(LoadShape.create_bitmap(0, 24, True, False))
        weekend = bin(LoadShape.create_bitmap(0, 24, False, True))
        zero = bin(LoadShape.create_bitmap(0, 24, False, False))
        three = bin(LoadShape.create_bitmap(12, 15, True, True))
        self.assertEqual(base, '0b' + '1'*48)
        self.assertEqual(weekday, '0b' + '1'*24)
        self.assertEqual(weekend, '0b' + '1'*24 + '0'*24)
        self.assertEqual(zero, '0b0')
        self.assertEqual(three, '0b'+'1'*3+'0'*21+'1'*3+'0'*12)

    def test_multiton(self):
        ls1 = LoadShape(1978, "test")
        ls2 = LoadShape(1978, "should ignore this name")
        self.assertEqual(ls2.name, "test")
        self.assertEqual(ls1, ls2)
        self.assertTrue(ls1 is ls2)

    def test_comparison(self):
        self.assertTrue(BASE != PEAK)
        self.assertTrue(PEAK == PEAK)

    def test_intersects(self):
        self.assertTrue(PEAK.intersects(BASE))
        self.assertFalse(PEAK.intersects(OFFPEAK))
        self.assertTrue(WEEKEND_OFFPEAK.intersects(OFFPEAK))
        self.assertFalse(PEAK.intersects(WEEKEND_PEAK))
        self.assertTrue(OFFPEAK.intersects(DAYTIME))
        self.assertFalse(NIGHTTIME.intersects(DAYTIME))
        self.assertTrue(EXTENDED_DAYTIME.intersects(WEEKEND))
        self.assertFalse(EXTENDED_PEAK.intersects(WEEKEND))
        self.assertTrue(WEEKDAY.intersects(EXTENDED_PEAK))
        self.assertFalse(WEEKDAY_OFFPEAK.intersects(WEEKEND_EXTENDED_PEAK))
        self.assertTrue(HOURS[1], EFAS[1])
        self.assertFalse(WEEKDAY_EFAS[4].intersects(NEVER_LS))

    def test_efa(self):
        self.assertTrue(HOURS[0].intersects(EFAS[0]))
        self.assertTrue(HOURS[1].intersects(EFAS[0]))
        self.assertTrue(HOURS[2].intersects(EFAS[0]))
        self.assertTrue(HOURS[3].intersects(EFAS[0]))
        self.assertFalse(HOURS[4].intersects(EFAS[0]))
        self.assertTrue(HOURS[4].intersects(EFAS[1]))
        self.assertTrue(OFFPEAK.intersects(EFAS[5]))
        self.assertFalse(WEEKDAY_OFFPEAK.intersects(EFAS[4]))
        self.assertTrue(PEAK.intersects(EFAS[4]))

    def test_contains(self):
        self.assertTrue(PEAK in BASE)
        self.assertFalse(PEAK in NIGHTTIME)
        self.assertTrue(NIGHTTIME in OFFPEAK)

    def test_difference(self):
        self.assertEqual(BASE.difference(OFFPEAK), PEAK)
        self.assertEqual(PEAK.difference(BASE), NEVER_LS)
        self.assertEqual(EXTENDED_PEAK.difference(PEAK), WEEKDAY_EFAS[5])

    def test_complement(self):
        self.assertEqual(PEAK.complement(), OFFPEAK)
        self.assertEqual(EFAS[3].complement().complement(), EFAS[3])
        self.assertEqual(NEVER_LS.complement(), BASE)

    def test_union(self):
        self.assertEqual(PEAK.union(OFFPEAK), BASE)
        self.assertEqual(WEEKEND.union(WEEKDAY_OFFPEAK), OFFPEAK)
        self.assertEqual(EFAS[0].union(EFAS[1]).union(EFAS[5]),
                         NIGHTTIME)

    def test_hours(self):
        self.assertTrue(HOURS[20] in NIGHTTIME)
        self.assertEqual(HOURS[0].union(HOURS[1]).union(HOURS[2])
                         .union(HOURS[3]), EFAS[0])
        self.assertTrue(HOURS[19] in DAYTIME)

        self.assertTrue(HOURS[7].is_hour)
        self.assertFalse(EFAS[3].is_hour)

        self.assertEqual(HOURS[12].hour, 12)
        two = LoadShape(LoadShape.create_bitmap(1, 3, True, False))
        self.assertFalse(two.is_hour)

    def test_intersection(self):
        self.assertEqual(PEAK.intersection(BASE), PEAK)
        self.assertEqual(PEAK.intersection(OFFPEAK), NEVER_LS)
        self.assertEqual(OFFPEAK.intersection(WEEKEND), WEEKEND)

    def test_partition(self):
        self.assertEqual(LoadShape.partition({PEAK}), {PEAK})
        BASE_PEAK = {BASE, PEAK}
        PEAK_OFFPEAK = {PEAK, OFFPEAK}
        self.assertEqual(LoadShape.partition(BASE_PEAK), PEAK_OFFPEAK)
        DT_NT = {DAYTIME, NIGHTTIME}
        self.assertEqual(LoadShape.partition(DT_NT), DT_NT)
        WD_WE = {WEEKDAY, WEEKEND}
        self.assertEqual(LoadShape.partition(WD_WE), WD_WE)
        WEOP_WDOP_WEPK = {WEEKEND_OFFPEAK, WEEKDAY_OFFPEAK, WEEKEND_PEAK}
        self.assertEqual(LoadShape.partition(WEOP_WDOP_WEPK), WEOP_WDOP_WEPK)
        WEOP_BASE_WDOP_WEPK = {WEEKEND_OFFPEAK, BASE, WEEKDAY_OFFPEAK,
                               WEEKEND_PEAK}
        WEOP_PEAK_WDOP_WEPK = {WEEKEND_OFFPEAK, PEAK, WEEKDAY_OFFPEAK,
                               WEEKEND_PEAK}
        self.assertEqual(LoadShape.partition(WEOP_BASE_WDOP_WEPK),
                         WEOP_PEAK_WDOP_WEPK)
        WDOP_WDP_WEOP_WEP = {WEEKEND_OFFPEAK, PEAK, WEEKEND_PEAK,
                            WEEKDAY_OFFPEAK}
        self.assertEqual(LoadShape.partition(WDOP_WDP_WEOP_WEP),
                         WDOP_WDP_WEOP_WEP)

        self.assertEqual(LoadShape.partition({}), set())

    def test_weekday_load_factor(self):
        self.assertEqual(BASE.weekday_load_factor, 1)
        self.assertEqual(WEEKDAY.weekday_load_factor, 1)
        self.assertEqual(WEEKEND.weekday_load_factor, 0)
        self.assertEqual(EFAS[0].weekday_load_factor, 4/24)
        self.assertEqual(WEEKDAY_EFAS[1].weekday_load_factor, 4/24)
        self.assertEqual(WEEKEND_EFAS[1].weekday_load_factor, 0)
        self.assertEqual(NEVER_LS.weekday_load_factor, 0)

    def test_weekend_load_factor(self):
        self.assertEqual(BASE.weekend_load_factor, 1)
        self.assertEqual(WEEKDAY.weekend_load_factor, 0)
        self.assertEqual(WEEKEND.weekend_load_factor, 1)
        self.assertEqual(EFAS[0].weekend_load_factor, 4/24)
        self.assertEqual(WEEKDAY_EFAS[1].weekend_load_factor, 0)
        self.assertEqual(WEEKEND_EFAS[1].weekend_load_factor, 4/24)
        self.assertEqual(NEVER_LS.weekend_load_factor, 0)

    def test_str(self):
        self.assertEqual(str(BASE), 'Base')
        self.assertEqual(str(NEVER_LS), 'Never')
        self.assertEqual(str(HOURS[7]), 'H07')
        self.assertEqual(str(HOURS[7].intersection(WEEKDAY)), 'Weekday-H07')
        self.assertEqual(str(HOURS[13].intersection(WEEKEND)), 'Weekend-H13')
        self.assertEqual(str(EFAS[3].intersection(WEEKDAY)), 'Weekday-EFA4')
        self.assertEqual(str(EFAS[3].intersection(WEEKEND)), 'Weekend-EFA4')
        self.assertEqual(str(EFAS[2]), 'EFA3')
        output = "weekdays: " + "0"*3 + "1"*4 + "0"*17 + "\n"
        output += "weekends: " + "0" * 24
        test = LoadShape.create_bitmap(3, 7, True, False)
        self.assertEqual(str(LoadShape(test)), output)

    def test_parse(self):
        self.assertEqual(LoadShape('Base'), BASE)
        self.assertEqual(LoadShape('Weekday-EFA4'), WEEKDAY_EFAS[3])
        self.assertEqual(LoadShape('H07'), HOURS[7])
        with self.assertRaises(ValueError):
            LoadShape('dummy')

    def test_iterator(self):
        expected = [LoadShape('Weekday-H12'),
                    LoadShape('Weekday-H13'),
                    LoadShape('Weekday-H14'),
                    LoadShape('Weekday-H15'),
                    LoadShape('Weekend-H12'),
                    LoadShape('Weekend-H13'),
                    LoadShape('Weekend-H14'),
                    LoadShape('Weekend-H15')]
        self.assertEqual([h for h in LoadShape('EFA4')], expected)


