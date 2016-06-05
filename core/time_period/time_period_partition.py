from core.time_period.date_range import DateRange
from core.time_period.load_shape import LoadShape
from core.time_period.load_shaped_date_range import LoadShapedDateRange

class DateRangePartition(object):
    '''Takes an iterable collection of DateRange objects and forms a
    partition using the equivalence relationship:
    
    dr1 == dr2 iff 