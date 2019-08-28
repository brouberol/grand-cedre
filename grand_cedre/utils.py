import datetime
import calendar


def start_of_month(year=None, month=None):
    if year and month:
        return datetime.datetime(year, month, 1, 0, 0, 0)

    now = datetime.datetime.utcnow()
    monthstart = now.replace(day=1, hour=0, minute=0, second=0)
    return monthstart


def end_of_month(year=None, month=None):
    if year and month:
        day = datetime.datetime(year, month, 1, 0, 0, 0)
    else:
        day = datetime.datetime.utcnow()
    _, last_day = calendar.monthrange(day.year, day.month)
    monthend = day.replace(day=last_day, hour=0, minute=0, second=0)
    return monthend
