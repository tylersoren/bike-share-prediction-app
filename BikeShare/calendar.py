from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday, \
    nearest_workday, previous_friday, next_monday, \
    USMartinLutherKingJr, USPresidentsDay, USMemorialDay, \
    USLaborDay, USThanksgivingDay

from pandas import DateOffset
from dateutil.relativedelta import TH
import datetime as dt

# Create Holiday Calendar
class USHolidayCalendar(AbstractHolidayCalendar):
        rules = [
            Holiday('NewYearsDay', month=1, day=1, observance=nearest_workday),
            USMartinLutherKingJr,
            USPresidentsDay,
            USMemorialDay,
            Holiday('USIndependenceDay', month=7, day=4, observance=nearest_workday),
            USLaborDay,
            USThanksgivingDay,
            Holiday('DayAfterThanksgiving', month=11, day=1, offset=[DateOffset(weekday=TH(4)), DateOffset(1)]),
            Holiday('ChristmasEve', month=12, day=24, observance=previous_friday),
            Holiday('Christmas', month=12, day=25, observance=next_monday)
        ]

# Return true if supplied date is a holiday
def is_holiday(date: dt.date):

    if str(date) in get_holidays(date.year).astype(str):
      return True
    else:
      return False


# Returns list of holiday dates
def get_holidays(year):
    cal = USHolidayCalendar()

    return cal.holidays(dt.datetime(year-1, 12, 31), dt.datetime(year, 12, 31))
