from unittest import mock
from datetime import datetime

from grand_cedre.utils import start_of_month, end_of_month


def test_start_of_month():
    assert start_of_month(2019, 1) == datetime(2019, 1, 1, 0, 0)


@mock.patch("grand_cedre.utils.utcnow")
def test_start_of_current_month(m_utcnow):
    m_utcnow.return_value = datetime(2019, 3, 17, 12, 3, 18)
    assert start_of_month() == datetime(2019, 3, 1, 0, 0)


def test_end_of_month():
    assert end_of_month(2019, 1) == datetime(2019, 1, 31, 0, 0)


@mock.patch("grand_cedre.utils.utcnow")
def test_end_of_current_month(m_utcnow):
    m_utcnow.return_value = datetime(2019, 3, 17, 12, 3, 18)
    assert end_of_month() == datetime(2019, 3, 31, 0, 0)
