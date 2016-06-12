# TODO: analyse whether the Pandas holiday calendars are useful, or is there a more efficient solution
# TODO: improve docstrings

import datetime as dt

DAYS_PER_YEAR = 365.0
END_OF_WORLD = dt.date.max - dt.timedelta(365)
START_OF_WORLD = dt.date.min


def time_between(start_date, end_date):
    """Calculates the time between two dates as a fraction of a year"""
    return (end_date - start_date).days / DAYS_PER_YEAR


def workdays(start_date,
             end_date,
             which_days={"Mon", "Tue", "Wed", "Thu", "Fri"},
             hol_cal=None):
    """
    Calculates the number of working days between two dates, inclusive
    (start_date <= end_date)

    The actual working days can be set with the optional which_days parameter
    """
    # first force which_days to be a set
    if type(which_days) == str:
        which_days = [which_days]
    if type(which_days) == list:
        which_days = set(which_days)

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_set = set(days)

    # then test the set has valid entries
    if not which_days.issubset(day_set):
        msg = "which_days contains {}: should be a set of strings of weekday names"\
                .format(which_days.difference(day_set))
        raise TypeError(msg)

    # calculate the number of full weeks within the period
    # and the corresponding num_workdays
    day_diff = (end_date - start_date).days
    full_weeks = int((day_diff - day_diff % 7) / 7)
    num_workdays = full_weeks * len(which_days)

    # calculate the number of residual days after taking out full weeks
    start_day = start_date.weekday()
    end_day = end_date.weekday()
    if start_day <= end_day:
        residual = set(days[start_day: end_day + 1])
    else:
        if full_weeks >= 0:
            residual = set(days[start_day:] + days[: end_day + 1])
        else:
            return 0  # the input range is empty since it ends before it starts

    # update the num_workdays with the number of which_days
    # within the residual_days
    num_workdays += len(residual.intersection(which_days))

    # if there's a holiday calendar, knock off any holidays in the date range
    # and in which_days
    if hol_cal is not None:
        hols = hol_cal.holidays(start_date, end_date)
        hols_in_whichdays = [days[hol.weekday()] in which_days for hol in hols]
        num_workdays -= sum(hols_in_whichdays)

    return num_workdays
