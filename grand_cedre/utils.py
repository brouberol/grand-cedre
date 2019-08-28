import datetime
import calendar


def start_of_current_month():
    now = datetime.datetime.utcnow()
    monthstart = now.replace(day=1, hour=0, minute=0, second=0)
    return monthstart


def end_of_current_month():
    now = datetime.datetime.utcnow()
    _, last_day = calendar.monthrange(now.year, now.month)
    monthend = now.replace(day=last_day, hour=0, minute=0, second=0)
    return monthend
