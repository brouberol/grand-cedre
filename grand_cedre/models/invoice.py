import datetime
import os

from jinja2 import Template
from babel.dates import format_date
from decimal import Decimal
from collections import defaultdict
from urllib.parse import urlencode

from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from grand_cedre.models import Base
from grand_cedre.models.booking import DailyBooking

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
template_dir = os.path.join(parent_dir, "templates")

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

    daily_bookings = relationship("DailyBooking", back_populates="invoice")
    client = relationship("Client", back_populates="invoices")

    def __str__(self):
        return f"{self.client} {self.period}: {self.total_price}{self.symbol}"

    @staticmethod
    def format_period(date=None):
        date = date or datetime.date.today()
        return f"{date.year}-{str(date.month).zfill(2)}"

    @property
    def symbol(self):
        return SYMBOLS[self.currency]

    @property
    def total_price(self):
        return sum([Decimal(booking.price) for booking in self.daily_bookings])

    @property
    def number(self):
        shortened_year = self.period.split("-")[0][2:]
        return f"GC {str(self.id).zfill(3)}-{shortened_year}"

    @property
    def bookings_per_room(self):
        out = defaultdict(dict)
        for booking in self.daily_bookings:
            if booking.duration not in out[booking.room]:
                out[booking.room][booking.duration] = RoomBookings([booking])
            else:
                out[booking.room][booking.duration].bookings.append(booking)
        return out

    @property
    def year(self):
        return int(self.period.split("-")[0])

    @property
    def month(self):
        return int(self.period.split("-")[0])

    @property
    def is_valid(self):
        return not self.client.missing_details()

    @property
    def filename(self):
        return f"{str(self.client).lower()}-{self.issued_at}.pdf".replace(" ", "-")

    def to_html(self, locale="fr_FR"):
        today = datetime.date.today()
        template_variables = {}
        template_variables["invoice"] = self
        template_variables["locale_month"] = format_date(today, "MMMM", locale=locale)
        template_variables["locale_year"] = today.year
        template_variables["locale_issue_date"] = format_date(
            self.issued_at, "dd MMMM YYYY", locale=locale
        )
        with open(os.path.join(template_dir, "invoice.html.j2")) as template_f:
            template = Template(template_f.read())
            invoice_content = template.render(**template_variables)
        return invoice_content

    def to_mailto_link(self):
        params = {}
        params["title"] = f"Votre facture du Grand Cèdre de {self.period}"
        with open(os.path.join(template_dir, "invoice-email.j2")) as template_f:
            template = Template(template_f.read())
            params["body"] = template.render(invoice=self)

        return f"mailto:{self.client.email}?{urlencode(params)}"
