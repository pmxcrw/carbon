
DAYS_PER_YEAR = 365.0


def time_between(start_date, end_date):
    '''Calculates the time between two dates as a fraction of a year'''
    return (end_date - start_date).days / DAYS_PER_YEAR


def workdays(start_date,
             end_date,
             whichdays={"Mon", "Tue", "Wed", "Thu", "Fri"},
             hol_cal=None):
    '''
    Calculates the number of working days between two dates, inclusive
    (start_date <= end_date)

    The actual working days can be set with the optional whichdays parameter
    '''
    # first force whichdays to be a set
    if type(whichdays) == str:
        whichdays = [whichdays]
    if type(whichdays) == list:
        whichdays = set(whichdays)

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_set = set(days)

    # then test the set has valid entries
    if not whichdays.issubset(day_set):
        msg = "whichdays contains {}: should be a set of strings of weekday names"\
                .format(whichdays.difference(day_set))
        raise TypeError(msg)

    # calculate the number of full weeks within the period
    # and the corresponding num_workdays
    day_diff = (end_date - start_date).days
    full_weeks = int((day_diff - day_diff % 7) / 7)
    num_workdays = full_weeks * len(whichdays)

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

    # update the num_workdays with the number of whichdays
    # within the residual_days
    num_workdays += len(residual.intersection(whichdays))

    # if there's a holiday calendar, knock off any holidays in the date range
    # and in whichdays
    if hol_cal is not None:
        hols = hol_cal.holidays(start_date, end_date)
        hols_in_whichdays = [days[hol.weekday()] in whichdays for hol in hols]
        num_workdays -= sum(hols_in_whichdays)

    return num_workdays
