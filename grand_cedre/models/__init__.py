from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from .booking import Booking
from .client import Client
from .invoice import Invoice
from .contract import Contract
from .room import Room
