from flask import url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from markupsafe import Markup
from wtforms.validators import ValidationError, Email
from sqlalchemy import or_

from . import app
from .db import db

from grand_cedre.models.booking import Booking
from grand_cedre.models.client import Client
from grand_cedre.models.invoice import Invoice
from grand_cedre.models.contract import (
    Contract,
    FlatRateContract,
    ExchangeContract,
    OneShotContract,
)


def validate_start_end_dates(form, field):
    if hasattr(form, "end_date"):
        if form.start_date.data >= form.end_date.data:
            raise ValidationError(
                "La date de début doit être antérieure à la date de fin"
            )


class GrandCedreView(ModelView):
    def search_placeholder(self):
        return "Recherche"


class ClientView(GrandCedreView):
    can_delete = False
    column_exclude_list = ["is_owner"]
    column_searchable_list = ("first_name", "last_name")
    form_excluded_columns = ("contracts", "bookings", "invoices")
    column_filters = ["first_name", "last_name", "address", "city", "zip_code"]
    column_labels = {
        "first_name": "Prénom",
        "last_name": "Nom",
        "address": "Adresse",
        "zip_code": "Code postal",
        "city": "Ville",
        "phone_number": "Numéro de téléphone",
    }
    form_excluded_columns = ["is_owner", "contracts", "bookings", "invoices"]
    form_args = {"email": {"validators": [Email()]}}


class ContractView(GrandCedreView):
    column_exclude_list = ["type"]
    column_searchable_list = ("client.first_name", "client.last_name")

    column_labels = {
        "client": "Client",
        "start_date": "Date de début",
        "booking_price": "Prix par réservation",
        "hourly_rate": "Taux horaire",
        "total_hours": "Heures réservées",
        "remaining_hours": "Heures restantes",
    }
    form_excluded_columns = ["type"]
    form_args = {"start_date": {"validators": [validate_start_end_dates]}}

    def get_query(self):

        return self.session.query(self.model).filter(
            self.model.type == self.model._type
        )


class BookingView(GrandCedreView):
    column_labels = {
        "client": "Client",
        "room": "Salle",
        "invoice": "Facture",
        "start_datetime": "Date de début",
        "end_datetime": "Date de fin",
        "start_date": "Date",
        "start_time": "Heure de début",
        "end_time": "Heure de fin",
        "calendar_link": "Lien",
        "price": "Prix",
        "frozen": "Consolidée",
    }
    column_list = [
        "client",
        "room",
        "start_date",
        "start_time",
        "end_time",
        "calendar_link",
        "price",
    ]
    column_filters = ["start_datetime", "end_datetime", "price"]
    column_searchable_list = (
        "client.first_name",
        "client.last_name",
        "room.name",
        "start_datetime",
    )
    column_formatters = {
        "calendar_link": (
            lambda v, c, m, p: Markup(
                f'<a href={m.calendar_link} target="_blank">📅</a>'
            )
        ),
        "start_date": lambda v, c, m, p: (f"{m.start_datetime.date()}"),
        "start_time": lambda v, c, m, p: (
            f"{m._format_time(m.start_datetime.time(), sep=':')}"
        ),
        "end_time": lambda v, c, m, p: (
            f"{m._format_time(m.end_datetime.time(), sep=':')}"
        ),
    }


class InvoiceView(GrandCedreView):
    def render_download_link(view, context, model, p):
        if model.is_valid:
            return Markup(
                f"<a href={url_for('download_invoice_as_pdf', invoice_id=model.id)}>💾</a>"
            )
        return ""

    def render_send_link(view, context, model, p):
        if model.is_valid:
            return Markup(f'<a href={model.to_mailto_link()} target="_blank">📧</a>')
        return ""

    can_delete = False
    column_searchable_list = ("client.first_name", "client.last_name")
    column_list = (
        "number",
        "client",
        Invoice.period,
        "total_price",
        Invoice.issued_at,
        "download",
        "send",
    )
    column_labels = {
        "number": "# Facture",
        "client": "Client",
        "period": "Période",
        "total_price": "Total",
        "issued_at": "Date d'édition",
        "download": "Télécharger",
        "currency": "Devise",
        "send": "Envoyer",
    }
    column_formatters = {
        "client": (lambda v, c, m, p: f"{m.client}"),
        "total_price": (lambda v, c, m, p: f"{m.total_price}{m.symbol}"),
        "download": render_download_link,
        "send": render_send_link,
    }


class HomeAdminView(AdminIndexView):
    def __init__(self, db, *args, **kwargs):
        self.db = db
        super().__init__(*args, **kwargs)

    @expose("/")
    def admin_home(self):
        warning_messages = []
        clients_with_missing_details = (
            self.db.session.query(Client)
            .filter(
                or_(
                    Client.first_name.is_(None),
                    Client.last_name.is_(None),
                    Client.address.is_(None),
                )
            )
            .all()
        )
        if clients_with_missing_details:
            warning_messages.append(
                (
                    "Certains clients n'ont pas de nom ou d'adresse renseignés, "
                    "ce qui bloquera la génération de facture"
                )
            )
        return self.render("admin/home.html", warning_messages=warning_messages)


admin = Admin(
    app, name="grand-cedre", template_mode="bootstrap3", index_view=HomeAdminView(db)
)

admin.add_view(ClientView(Client, db.session, "Clients"))
admin.add_view(ContractView(Contract, db.session, "Standards", category="Contrats"))
admin.add_view(
    ContractView(
        OneShotContract, db.session, "Réservations occasionelles", category="Contrats"
    )
)
admin.add_view(
    ContractView(ExchangeContract, db.session, "Échanges", category="Contrats")
)
admin.add_view(
    ContractView(FlatRateContract, db.session, "Forfait", category="Contrats")
)
admin.add_view(BookingView(Booking, db.session, "Réservations"))
admin.add_view(InvoiceView(Invoice, db.session, "Factures"))
