import pytest

from decimal import Decimal

from grand_cedre.pricing import booking_price, Duration, NoMatchingPrice


@pytest.mark.parametrize(
    "duration, individual, expected",
    [
        (Duration.ONE_HOUR, True, "10.90"),
        (Duration.ONE_HOUR_AND_HALF, True, "15.00"),
        (Duration.ONE_HOUR, False, "15.65"),
        (Duration.ONE_HOUR_AND_HALF, False, "20.45"),
    ],
)
def test_booking_price(duration, individual, expected):
    assert booking_price(duration, individual) == Decimal(expected)


def test_no_price_found():
    with pytest.raises(NoMatchingPrice):
        booking_price(Duration.TWO_HOURS, individual=True)
