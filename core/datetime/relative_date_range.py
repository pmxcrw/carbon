import datetime as dt
from core.datetime.date_range import DateRange


class RelativeDateRange(object):

    def __init__(self, range_type, offset=1):
        range_type = range_type.lower().strip()
        self.offset = offset
        for known_relative_range_type in RelativeRangeType.__subclasses__():
            if range_type in known_relative_range_type.aliases:
                self.range_type = known_relative_range_type
                break
        else:
            msg = "range type unknown, should be a member of the"
            msg += " alias set for a subclass of RelativeRangeType object"
            raise ValueError(msg)

    def fix(self, obs_date):
        return self.range_type.fix(obs_date, self.offset)

    def __str__(self):
        return self.range_type.str + "(offset={})".format(self.offset)


class RelativeRangeType(object):

    @staticmethod
    def fix(obs_date, offset):
        raise NotImplementedError


class CalendarDayAheadType(RelativeRangeType):

    aliases = {'calendardayahead', 'calendar_day_ahead', "d1", "cal_day_ahead",
               'caldayahead', 'cal_da', 'calendar_da',
               'calendarda', 'cda', 'calda'}

    str = "CalendarDayAhead"

    @staticmethod
    def fix(obs_date, offset):
        date = obs_date + dt.timedelta(offset)
        return DateRange(date, date)


class DayAheadType(RelativeRangeType):

    aliases = {'da', 'day_ahead', 'dayahead', 'daya'}

    str = "DayAhead"

    @staticmethod
    def fix(obs_date, offset):
        direction = 1
        if offset < 0:
            direction = -1
        weekday = obs_date.weekday()
        if weekday > 4:
            if offset > 0:
                obs_date += dt.timedelta(7 - weekday)
                offset -= 1
            elif offset < 0:
                obs_date += dt.timedelta(4 - weekday)
                offset +=1
            else:
                msg = "offset of zero and an obs_date falling in a weekend is "
                msg += "ambiguous for a DA fix"
                raise ValueError(msg)
        weekends = abs(offset) // 5
        residual = direction * (abs(offset) % 5)
        weekday = obs_date.weekday() + residual
        if weekday < 0 or weekday > 4:
            weekends += 1
        obs_date += dt.timedelta(offset + 2 * direction * weekends)
        return DateRange(obs_date, obs_date)


class WeekendAheadType(RelativeRangeType):

    aliases = {'weekendahead', 'weekend_ahead', 'wendahead', 'wend_ahead',
               'wkend_ahead', 'wkendahead', 'weekenda', 'wkenda', 'wenda'}

    str = "WeekendAhead"

    @staticmethod
    def fix(obs_date, offset):
        weekday = obs_date.weekday()
        if offset > 0:
            offset -= 1
            if weekday > 4:
                start = obs_date + dt.timedelta(12 - weekday)
            else:
                start = obs_date + dt.timedelta(5 - weekday)
        elif offset < 0:
            offset += 1
            start = obs_date - dt.timedelta(2 + weekday)
        else:
            if weekday == 5:
                return DateRange(obs_date, obs_date + dt.timedelta(1))
            elif weekday == 6:
                return DateRange(obs_date - dt.timedelta(1), obs_date)
            else:
                raise ValueError("offset of zero is ambiguous")
        start += dt.timedelta(offset * 7)
        return DateRange(start, start + dt.timedelta(1))


class WeekAheadType(RelativeRangeType):

    aliases = {'wa', 'w_ahead', 'week_ahead', 'wk_ahead',
               'wahead', 'weekahead', 'wkahead'}

    str = "WeekAhead"

    @staticmethod
    def fix(obs_date, offset):
        if offset == 0:
            return DateRange(start=obs_date, range_type='W')
        if offset != 0:
            return DateRange(start=obs_date, range_type='W').offset(offset)


class MonthAheadType(RelativeRangeType):

    aliases = {'ma', 'month_ahead', 'mth_ahead', 'm_ahead',
               'month_a', 'mth_a', 'm_a', 'montha', 'mtha',
               'monthahead', 'mthahead', 'mahead'}

    str = "MonthAhead"

    @staticmethod
    def fix(obs_date, offset):
        if offset == 0:
            return DateRange(start=obs_date, range_type='M')
        if offset != 0:
            return DateRange(start=obs_date, range_type='M').offset(offset)


class QuarterAheadType(RelativeRangeType):

    aliases = {'qa', 'quarter_ahead', 'qtr_ahead', 'q_ahead',
               'quarter_a', 'qtr_a', 'q_a', 'quartera', 'qtra',
               'quaterahead', 'qtrahead', 'qahead'}

    str = "QuarterAhead"

    @staticmethod
    def fix(obs_date, offset):
        if offset == 0:
            return DateRange(start=obs_date, range_type='Q')
        if offset != 0:
            return DateRange(start=obs_date, range_type='Q').offset(offset)


class SeasonAheadType(RelativeRangeType):

    aliases = {'sa', 'season_ahead', 'sea_ahead', 's_ahead',
               'season_a', 'sea_a', 's_a', 'seasona', 'seaa',
               'seasonahead', 'seaahead', 'sahead'}

    str = "SeasonAhead"

    @staticmethod
    def fix(obs_date, offset):
        range_type = "sum"
        try:
            output = DateRange(start=obs_date, range_type=range_type)
        except:
            range_type = "win"
            output = DateRange(start=obs_date, range_type=range_type)
        if offset == 0:
            return output
        if offset != 0:
            return output.offset(offset)


class SummerAheadType(RelativeRangeType):

    aliases = {'suma', 'summer_ahead', 'sum_ahead',
               'summer_a', 'sum_a', 'summera', 'suma',
               'summerahead', 'sumahead'}

    str = "SummerAhead"

    @staticmethod
    def fix(obs_date, offset):
        offset *= 2
        range_type = "sum"
        try:
            output = DateRange(start=obs_date, range_type=range_type)
        except:
            range_type = "win"
            output = DateRange(start=obs_date, range_type=range_type)
        if offset == 0:
            if range_type == "sum":
                return output
            else:
                raise ValueError("obs_date in winter, so offset can't be zero")
        elif offset > 0:
            if range_type == "win":
                offset -= 1
        elif offset < 0:
            if range_type == "win":
                offset += 1
        return output.offset(offset)


class WinterAheadType(RelativeRangeType):

    aliases = {'wina', 'winter_ahead', 'win_ahead',
               'winter_a', 'win_a', 'wintera', 'wina',
               'winterahead', 'winahead'}

    str = "WinterAhead"

    @staticmethod
    def fix(obs_date, offset):
        offset *= 2
        range_type = "win"
        try:
            output = DateRange(start=obs_date, range_type=range_type)
        except:
            range_type = "sum"
            output = DateRange(start=obs_date, range_type=range_type)
        if offset == 0:
            if range_type == "win":
                return output
            else:
                raise ValueError("obs_date in summer, so offset can't be zero")
        elif offset > 0:
            if range_type == "sum":
                offset -= 1
        elif offset < 0:
            if range_type == "sum":
                offset += 1
        return output.offset(offset)


class YearAheadType(RelativeRangeType):

    aliases = {'ya', 'year_ahead', 'yr_ahead', 'y_ahead',
               'year_a', 'yr_a', 'y_a', 'yeara', 'yra',
               'yearahead', 'yrahead', 'yahead'}

    str = "YearAhead"

    @staticmethod
    def fix(obs_date, offset):
        if offset == 0:
            return DateRange(start=obs_date, range_type='Y')
        if offset != 0:
            return DateRange(start=obs_date, range_type='Y').offset(offset)


class GasYearAheadType(RelativeRangeType):

    aliases = {'gya', 'gasyear_ahead', 'gyr_ahead', 'gy_ahead',
               'gasyear_a', 'gyr_a', 'gy_a', 'gasyeara', 'gyra',
               'gasyearahead', 'gyrahead', 'gyahead', 'gas_year_ahead',
               'gas_year_a', 'gas_yr_ahead', 'gas_ya', 'gas_yra'}

    str = "GasYearAhead"

    @staticmethod
    def fix(obs_date, offset):
        if offset == 0:
            return DateRange(start=obs_date, range_type='GY')
        if offset != 0:
            return DateRange(start=obs_date, range_type='GY').offset(offset)


class BalanceOfMonthType(RelativeRangeType):

    aliases = {'balmo', 'bal_mth', 'balance_of_month', 'bal_of_month',
               'balanceofmonth', 'balmth', 'balm', 'bm', 'bmth', 'b_mth'}

    str = "BalanceOfMonth"

    @staticmethod
    def fix(obs_date, offset):
        '''ignores offset'''
        if obs_date.month == 12:
            year = obs_date.year + 1
            month = 1
        else:
            year = obs_date.year
            month = obs_date.month + 1
        month_end = dt.date(year, month, 1) - dt.timedelta(1)
        return DateRange(obs_date, month_end)


class DecemberAhead(RelativeRangeType):

    aliases = {'decahead', 'dec_ahead', 'decemberahead', 'december_ahead',
               'deca', 'dec_a', 'decembera', 'december_a'}

    str = "DecemberAhead"

    @staticmethod
    def fix(obs_date, offset):
        if offset == 0:
            if obs_date.month != 12:
                raise ValueError("obs_date not in December, offset of zero invalid")
            else:
                return DateRange(start=obs_date, range_type='m')
        else:
            if obs_date.month != 12:
                if offset > 0:
                    offset -= 1
                output = dt.date(obs_date.year + offset, 12, 1)
            else:
                output = dt.date(obs_date.year + offset, 12, 1)
            return DateRange(start=output, range_type='m')

