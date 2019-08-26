from decimal import Decimal
from enum import Enum


class NoMatchingPrice(Exception):
    pass


# Todo: move this in DB?
# Support changing price


class Duration(Enum):
    ONE_HOUR = 1
    ONE_HOUR_AND_HALF = 1.5
    TWO_HOURS = 2
    TWO_HOURS_AND_HALF = 2.5
    THREE_HOURS = 3
    HALF_DAY = 4.5
    WHOLE_DAY = 8
    # WEEKEND = 16
    # PREPAID = 40

    @classmethod
    def from_hour(cls, nb_hour):
        return cls._value2member_map_[nb_hour]


COLLECTIVE_ROOM_PRICES = {
    Duration.ONE_HOUR: Decimal("15.65"),
    Duration.ONE_HOUR_AND_HALF: Decimal("20.45"),
    Duration.TWO_HOURS: Decimal("26.55"),
    Duration.TWO_HOURS_AND_HALF: Decimal("32.00"),
    Duration.THREE_HOURS: Decimal("36.75"),
    Duration.HALF_DAY: Decimal("51.75"),
    Duration.WHOLE_DAY: Decimal("87.15"),
    "weekend": Decimal("156.60"),
}

COLLECTIVE_ROOM_PRICES_HOURLY = {
    Duration.ONE_HOUR: Decimal("15.65"),
    Duration.ONE_HOUR_AND_HALF: Decimal("13.62"),
    Duration.TWO_HOURS: Decimal("13.21"),
    Duration.TWO_HOURS_AND_HALF: Decimal("12.80"),
    Duration.THREE_HOURS: Decimal("12.26"),
    Duration.HALF_DAY: Decimal("11.50"),
    Duration.WHOLE_DAY: Decimal("10.90"),
    "weekend": Decimal("9.78"),
}

INDIVIDUAL_ROOM_PRICES = {
    Duration.ONE_HOUR: Decimal("10.90"),
    Duration.ONE_HOUR_AND_HALF: Decimal("15.00"),
    Duration.HALF_DAY: Decimal("40.50"),
    Duration.WHOLE_DAY: Decimal("68.00"),
    "prepaid": Decimal("360.00"),
}

INDIVIDUAL_ROOM_PRICES_HOURLY = {
    Duration.ONE_HOUR: Decimal("10.90"),
    Duration.ONE_HOUR_AND_HALF: Decimal("10.00"),
    Duration.HALF_DAY: Decimal("9.00"),
    Duration.WHOLE_DAY: Decimal("8.50"),
    "prepaid": Decimal("9.00"),
}


def _booking_price(duration, pricing):
    try:
        return pricing[duration]
    except KeyError:
        # This happens when someone has booked for a slot
        # for which we don't have an exact pricing for
        # ex: 2h in an individual room
        raise NoMatchingPrice(
            f"No pricing could be easily found for duration {duration}"
        )


def booking_price(duration, individual=True):
    if individual:
        return _booking_price(duration, INDIVIDUAL_ROOM_PRICES)
    else:
        return _booking_price(duration, COLLECTIVE_ROOM_PRICES)
