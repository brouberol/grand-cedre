from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PolymorphicBase(Base):
    __abstract__ = True
    __mapper_args__ = {"polymorphic_on": "type"}

    def __init__(self, *args, **kwargs):
        self.type = self._type
        self.__mapper_args__["polymorphic_identity"] = self._type
        super().__init__(*args, **kwargs)


from .booking import Booking
from .client import Client
from .invoice import Invoice
from .contract import Contract
from .room import Room
