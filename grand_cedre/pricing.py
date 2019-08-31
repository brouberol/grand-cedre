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

    def __str__(self):
        translations = {
            "ONE_HOUR": "1h",
            "ONE_HOUR_AND_HALF": "1.5h",
            "TWO_HOURS": "2h",
            "THREE_HOURS": "3h",
            "HALF_DAY": "demi-journée",
            "WHOLE_DAY": "journée entière",
        }
        return translations[self._name_]

    @classmethod
    def from_hour(cls, nb_hour):
        return cls._value2member_map_[nb_hour]


COLLECTIVE_ROOM_PRICES = {
    Duration.ONE_HOUR: "15.65",
    Duration.ONE_HOUR_AND_HALF: "20.45",
    Duration.TWO_HOURS: "26.55",
    Duration.TWO_HOURS_AND_HALF: "32.00",
    Duration.THREE_HOURS: "36.75",
    Duration.HALF_DAY: "51.75",
    Duration.WHOLE_DAY: "87.15",
    "weekend": "156.60",
}

COLLECTIVE_ROOM_PRICES_HOURLY = {
    Duration.ONE_HOUR: "15.65",
    Duration.ONE_HOUR_AND_HALF: "13.62",
    Duration.TWO_HOURS: "13.21",
    Duration.TWO_HOURS_AND_HALF: "12.80",
    Duration.THREE_HOURS: "12.26",
    Duration.HALF_DAY: "11.50",
    Duration.WHOLE_DAY: "10.90",
    "weekend": "9.78",
}

INDIVIDUAL_ROOM_PRICES = {
    Duration.ONE_HOUR: "10.90",
    Duration.ONE_HOUR_AND_HALF: "15.00",
    Duration.HALF_DAY: "40.50",
    Duration.WHOLE_DAY: "68.00",
    "prepaid": "360.00",
}

INDIVIDUAL_ROOM_PRICES_HOURLY = {
    Duration.ONE_HOUR: "10.90",
    Duration.ONE_HOUR_AND_HALF: "10.00",
    Duration.HALF_DAY: "9.00",
    Duration.WHOLE_DAY: "8.50",
    "prepaid": "9.00",
}


def _booking_price(duration, pricing):
    try:
        return Decimal(pricing[duration])
    except KeyError:
        # This happens when someone has booked for a slot
        # for which we don't have an exact pricing for
        # ex: 2h in an individual room
        raise NoMatchingPrice(f"No pricing could be found for duration {duration}")


def booking_price(booking_duration, individual):
    if individual:
        return _booking_price(booking_duration, INDIVIDUAL_ROOM_PRICES)
    else:
        return _booking_price(booking_duration, COLLECTIVE_ROOM_PRICES)
