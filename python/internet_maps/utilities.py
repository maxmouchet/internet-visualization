from datetime import datetime


def closest_collector_date(date: datetime) -> datetime:
    hour = date.hour
    # TODO
    hour = 0
    # if hour % 2 != 0:
    #     hour = hour - 1
    return date.replace(hour=hour, minute=0, second=0, microsecond=0)
