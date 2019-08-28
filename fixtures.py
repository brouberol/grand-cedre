from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from grand_cedre.models import Base
from grand_cedre.models.client import Client
from grand_cedre.models.contract import Contract
from grand_cedre.models.room import Room
from grand_cedre.models.booking import Booking
from grand_cedre.models.invoice import Invoice

engine = create_engine("sqlite:///data/data.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

session.add(
    Client(
        first_name="Clémentine",
        last_name="Barthélemy",
        email="clembart@gmail.com",
        is_owner=True,
    )
)
session.add(
    Client(first_name="Isabelle", last_name="Albans", email="isalbans@gmail.com")
)
session.add(
    Client(first_name="Sylvie", last_name="Paulet", email="sylvie.paulet71@gmail.com")
)
session.add(
    Client(first_name="Marion", last_name="Garsiot", email="mariongarsiot3@gmail.com")
)
session.add(Client(first_name="MDO", last_name="Sarteel", email="mdosarteel@gmail.com"))
v = Client(first_name="Vincent", last_name="Grizard", email="vgrizard@gmail.com")
session.add(v)
session.add(
    Client(first_name="Claude", last_name="B", email="mediation.bclaude@gmail.com")
)
session.add(
    Client(
        first_name="Charline",
        last_name="Berthier",
        email="charlineberthierosteo@gmail.com",
    )
)
session.add(
    Client(first_name="Eliott", last_name="Sacha", email="eliottsacha71@gmail.com")
)

session.add(
    Contract(
        client=v,
        start_date=date(2019, 1, 1),
        end_date=date(2019, 12, 31),
        booking_duration=2.0,
        hourly_rate=9.25,
    )
)
session.commit()
