from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from grand_cedre.models import GrandCedreBase


class Client(GrandCedreBase):
    __tablename__ = GrandCedreBase.get_table_name("Client")
    __table_args__ = (UniqueConstraint("first_name", "last_name", "email"),)

    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    address = Column(String)
    zip_code = Column(String)
    city = Column(String)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, unique=True)
    is_owner = Column(Boolean, default=False)

    contracts = relationship("Contract", back_populates="client")
    daily_bookings = relationship("DailyBooking", back_populates="client")

    def __repr__(self):
        return f"<{self.__class__.__name__}: {str(self)}: {self.email}>"

    def __str__(self):
        if not all((self.first_name, self.last_name)):
            return self.email
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def missing_details(self):
        return not all(
            (self.first_name, self.last_name, self.address, self.zip_code, self.city)
        )
