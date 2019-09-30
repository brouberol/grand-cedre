import datetime
import os
import zipfile

from babel.dates import format_date
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.types import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from grand_cedre.models import GrandCedreBase
from grand_cedre.models.client import Client
from grand_cedre.models.types import RoomTypeEnum
from grand_cedre.utils import create_temporary_copy


parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
template_dir = os.path.join(parent_dir, "templates")
output_dir = os.path.join(parent_dir, "output")
static_dir = os.path.join(parent_dir, "static")


class Contract(GrandCedreBase):
    __tablename__ = GrandCedreBase.get_table_name("Contract")
    __table_args__ = (UniqueConstraint("client_id", "start_date", "room_type"),)

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    client_id = Column(Integer, GrandCedreBase.fk("Client"))
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    room_type = Column(SQLEnum(RoomTypeEnum))
    pricing_id = Column(Integer, GrandCedreBase.fk("FlatRatePricing"))
    recurring_pricing_id = Column(Integer, GrandCedreBase.fk("RecurringPricing"))
    total_hours = Column(String, nullable=True)
    remaining_hours = Column(String, nullable=True)
    weekly_hours = Column(Integer, nullable=True)

    client = relationship("Client", back_populates="contracts")
    invoices = relationship("Invoice", back_populates="contract")
    flat_rate_pricing = relationship("FlatRatePricing", back_populates="contracts")
    recurring_pricing = relationship("RecurringPricing", back_populates="contracts")

    def __str__(self):
        return f"{str(self.client)}: {self.start_date}: {self.type}:{self.room_type}"

    def filename(self, extension="odt"):
        return (
            f"contrat-{self.client.full_name.replace(' ', '-')}-"
            f"{datetime.date.today()}.{extension}"
        )

    def to_odt(self, jinja_env, locale="fr_FR"):
        today = datetime.date.today()
        template_variables = {}
        template_variables["contract"] = self
        template_variables["locale_today"] = format_date(
            today, "dd MMMM YYYY", locale=locale
        )
        with open(os.path.join(template_dir, "contract.xml.j2")) as template_f:
            template = jinja_env.from_string(template_f.read())
            contract_content = template.render(**template_variables)

        contract_odt_copy_path = create_temporary_copy(
            os.path.join(static_dir, "contract.odt")
        )

        with zipfile.ZipFile(contract_odt_copy_path, mode="a") as contract_odt:
            contract_odt.writestr("content.xml", contract_content)

        with open(contract_odt_copy_path, mode="rb") as out_file:
            out = out_file.read()

        os.unlink(contract_odt_copy_path)
        return out
