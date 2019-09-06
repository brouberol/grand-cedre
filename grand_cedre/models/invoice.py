import datetime
import os

from jinja2 import Template
from babel.dates import format_date
from decimal import Decimal
from urllib.parse import urlencode

from sqlalchemy import Column, Integer, String, ForeignKey, Date, event
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from grand_cedre.models import GrandCedreBase
from grand_cedre.models.booking import DailyBooking
from grand_cedre.models.types import ContractType
from grand_cedre.models.contract import Contract


parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
template_dir = os.path.join(parent_dir, "templates")

CURRENCIES = {"EURO": "EURO"}
SYMBOLS = {"EURO": "€"}


class Invoice(GrandCedreBase):

    __tablename__ = GrandCedreBase.get_table_name("Invoice")
    __table_args__ = (UniqueConstraint("contract_id", "period"),)

    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, GrandCedreBase.fk("Contract"))
    period = Column(String)
    issued_at = Column(Date)
    currency = Column(String, default="EURO")
    payed_at = Column(Date)
    check_number = Column(String)
    wire_transfer_number = Column(String)

    daily_bookings = relationship("DailyBooking", back_populates="invoice")
    contract = relationship("Contract", back_populates="invoices")

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
        if self.contract.type == ContractType.flat_rate:
            if self.contract.flat_rate_pricing:
                return Decimal(self.contract.flat_rate_pricing.flat_rate) * Decimal(
                    self.contract.flat_rate_pricing.prepaid_hours
                )
        elif self.contract.type == ContractType.recurring:
            if self.contract.recurring_pricing is not None:
                return self.contract.recurring_pricing.monthly_price
        return sum([Decimal(booking.price) for booking in self.daily_bookings])

    @property
    def number(self):
        shortened_year = self.period.split("-")[0][2:]
        return f"GC {str(self.id).zfill(3)}-{shortened_year}-A"

    @property
    def year(self):
        return int(self.period.split("-")[0])

    @property
    def month(self):
        return int(self.period.split("-")[0])

    @property
    def is_valid(self):
        return (
            not self.contract.client.missing_details() and self.total_price is not None
        )

    @property
    def filename(self):
        return f"{str(self.contract.client).lower()}-{self.issued_at}.pdf".replace(
            " ", "-"
        )

    def to_html(self, jinja_env, locale="fr_FR"):
        today = datetime.date.today()
        template_variables = {}
        template_variables["invoice"] = self
        template_variables["locale_month"] = format_date(today, "MMMM", locale=locale)
        template_variables["locale_year"] = today.year
        template_variables["locale_issue_date"] = format_date(
            self.issued_at, "dd MMMM YYYY", locale=locale
        )
        with open(os.path.join(template_dir, "invoice.html.j2")) as template_f:
            template = jinja_env.from_string(template_f.read())
            invoice_content = template.render(**template_variables)
        return invoice_content

    def to_mailto_link(self):
        params = {}
        params["title"] = f"Votre facture du Grand Cèdre de {self.period}"
        with open(os.path.join(template_dir, "invoice-email.j2")) as template_f:
            template = Template(template_f.read())
            params["body"] = template.render(invoice=self)

        return f"mailto:{self.contract.client.email}?{urlencode(params)}"


@event.listens_for(Contract, "after_insert")
def before_booking_delete(mapper, connection, target):
    if target.type == ContractType.flat_rate:
        period = (
            f"{Invoice.format_period(target.start_date)}-"
            f"{Invoice.format_period(target.end_date)}"
        )
        insert_invoice_q = f"""
        INSERT INTO {Invoice.__tablename__}
        (contract_id, period, issued_at, currency)
        VALUES({target.id}, '{period}', '{datetime.date.today()}', 'EURO')
        """
        connection.execute(insert_invoice_q)
