import datetime as dt

DAYS_PER_YEAR = 365.0
END_OF_WORLD = dt.date.max - dt.timedelta(365)
START_OF_WORLD = dt.date.min
MINUTES_PER_HOUR = 60
SECONDS_PER_DAY = 86400
MINUTES_PER_DAY = 60 * 24
SECONDS_PER_MINUTE = 60
HOURS_PER_DAY = 24

# TODO
# set up a dict that holds all the static data in the various time periods
# then in the core, loop through the dict and intialise all the objects
# use e.g.

# for name, value in static_dict.items():
#   vars()[name] = value