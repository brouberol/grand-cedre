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


class ClientView(ModelView):
    column_exclude_list = ["is_owner"]
    column_searchable_list = ("first_name", "last_name")
    form_excluded_columns = ("contracts", "bookings", "invoices")
    column_labels = {
        "first_name": "Prénom",
        "last_name": "Nom",
        "address": "Adresse",
        "zip_code": "Code postal",
        "city": "Ville",
    }


class ContractView(ModelView):
    column_searchable_list = ("client.first_name", "client.last_name")

    column_labels = {
        "client": "Client",
        "start_date": "Date de début",
        "end_date": "Date de fin",
        "booking_duration": "Durée du créneau",
        "hourly_rate": "Taux horaire",
    }


class BookingView(ModelView):
    column_labels = {
        "client": "Client",
        "room": "Salle",
        "invoice": "Facture",
        "start_date": "Date",
        "start_time": "Heure de début",
        "end_time": "Heure de fin",
        "calendar_link": "Lien",
        "price": "Prix",
        "frozen": "Consolidée",
    }
    column_list = column_labels.keys()

    column_searchable_list = (
        "client.first_name",
        "client.last_name",
        "room.name",
        "start_datetime",
    )
    column_formatters = {
        "calendar_link": (
            lambda v, c, m, p: Markup(f"<a href={m.calendar_link}>lien</a>")
        ),
        "start_date": lambda v, c, m, p: (f"{m.start_datetime.date()}"),
        "start_time": lambda v, c, m, p: (
            f"{m._format_time(m.start_datetime.time(), sep=':')}"
        ),
        "end_time": lambda v, c, m, p: (
            f"{m._format_time(m.end_datetime.time(), sep=':')}"
        ),
    }


class InvoiceView(ModelView):
    column_searchable_list = ("client.first_name", "client.last_name")
    column_list = ("client", Invoice.period, "total_price", Invoice.issued_at)
    column_labels = {
        "client": "Client",
        "period": "Période",
        "total_price": "Total",
        "issued_at": "Date d'édition",
    }
    column_formatters = {
        "client": (lambda v, c, m, p: f"{m.client}"),
        "total_price": (lambda v, c, m, p: f"{m.total_price}{m.symbol}"),
    }


admin.add_view(ClientView(Client, db.session, "Clients"))
admin.add_view(ContractView(Contract, db.session, "Contrats"))
admin.add_view(BookingView(Booking, db.session, "Réservations"))
admin.add_view(InvoiceView(Invoice, db.session, "Factures"))
