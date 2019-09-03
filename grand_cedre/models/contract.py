from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.types import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.ext.declarative import ConcreteBase
from decimal import Decimal

from grand_cedre.models import GrandCedreBase
from grand_cedre.models.client import Client

from grand_cedre.models.types import ContractType, RoomTypeEnum


class Contract(GrandCedreBase):
    __tablename__ = GrandCedreBase.get_table_name("Contract")
    __table_args__ = (UniqueConstraint("client_id", "start_date", "room_type"),)

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"))
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    room_type = Column(SQLEnum(RoomTypeEnum))
    pricing_id = Column(Integer, ForeignKey("pricings_flat_rate.id"))
    total_hours = Column(String, nullable=True)
    remaining_hours = Column(String, nullable=True)

    client = relationship("Client", back_populates="contracts")
    invoices = relationship("Invoice", back_populates="contract")
    flat_rate_pricing = relationship("FlatRatePricing", back_populates="contracts")

    def __str__(self):
        return f"{str(self.client)}: {self.start_date}: {self.type}:{self.room_type}"
