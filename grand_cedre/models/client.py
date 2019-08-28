from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint


from grand_cedre.models import Base


class Client(Base):

    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("first_name", "last_name", "email"),)

    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    address = Column(String)
    zip_code = Column(String)
    city = Column(String)
    email = Column(String, unique=True)
    is_owner = Column(Boolean, default=False)

    contracts = relationship("Contract", back_populates="client")
    bookings = relationship("Booking", back_populates="client")
    invoices = relationship("Invoice", back_populates="client")

    def __repr__(self):
        return f"<{self.__class__.__name__}: {str(self)}: {self.email}>"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def missing_details(self):
        return not all(
            (self.first_name, self.last_name, self.address, self.zip_code, self.city)
        )
