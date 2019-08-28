import datetime
import os

from weasyprint import HTML
from jinja2 import Template
from babel.dates import format_date
from decimal import Decimal
from collections import defaultdict

from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from grand_cedre.models import Base
from grand_cedre.models.booking import Booking

current_dir = os.path.abspath(os.path.dirname(__file__))

CURRENCIES = {"EURO": "EURO"}
SYMBOLS = {"EURO": "€"}


class RoomBookings(object):
    def __init__(self, bookings):
        self.bookings = bookings

    @property
    def price(self):
        return sum([Decimal(booking.price) for booking in self.bookings])

    @property
    def duration_in_hours(self):
        return sum([booking.duration_in_hour for booking in self.bookings])

    @property
    def count(self):
        return len(self.bookings)


class Invoice(Base):

    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("client_id", "period"),)

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    period = Column(String)
    issued_at = Column(Date)
    currency = Column(String, default="EURO")

    bookings = relationship("Booking", back_populates="invoice")
    client = relationship("Client", back_populates="invoices")

    def __str__(self):
        return f"{self.client} {self.period}: {self.total_price}{self.symbol}"

    def __repr__(self):
        return f"<{self.__class__.__name__} {str(self)}>"
