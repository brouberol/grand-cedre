from flask import Flask
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.sqla import ModelView
from markupsafe import Markup

from grand_cedre.models.client import Client
from grand_cedre.models.contract import Contract
from grand_cedre.models.room import Room
from grand_cedre.models.booking import Booking
from grand_cedre.models.invoice import Invoice


app = Flask("grand-cedre")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data/data.db"
app.config["FLASK_ADMIN_SWATCH"] = "flatly"
app.config[
    "SECRET_KEY"
] = b"\ry\xe0\x97\xe88\xed\x84\x05\xfdfN\x1daQ\xf8\x83!\xeanp\x80R\xd1"

db = SQLAlchemy(app)
admin = Admin(app, name="grand-cedre", template_mode="bootstrap3")


class BookingView(ModelView):
    column_formatters = {
        "calendar_link": (
            lambda v, c, m, p: Markup(f"<a href={m.calendar_link}>link</a>")
        ),
        "start_datetime": lambda v, c, m, p: (
            f"{m.start_datetime.date()}:{m._format_time(m.start_datetime.time(), sep=':')}"
        ),
        "end_datetime": lambda v, c, m, p: (
            f"{m.end_datetime.date()}:{m._format_time(m.end_datetime.time(), sep=':')}"
        ),
    }


class InvoiceView(ModelView):
    column_list = ("client", Invoice.period, "total_price", Invoice.issued_at)
    column_formatters = {
        "client": (lambda v, c, m, p: f"{m.client}"),
        "total_price": (lambda v, c, m, p: f"{m.total_price}{m.symbol}"),
    }


admin.add_view(ModelView(Client, db.session))
admin.add_view(ModelView(Contract, db.session))
admin.add_view(BookingView(Booking, db.session))
admin.add_view(ModelView(Room, db.session))
admin.add_view(InvoiceView(Invoice, db.session))
