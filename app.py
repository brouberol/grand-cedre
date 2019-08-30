import tempfile
import os

from weasyprint import HTML
from flask import Flask, abort, make_response, url_for, redirect
from flask_admin import Admin, AdminIndexView, expose
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.sqla import ModelView
from flask_babelex import Babel
from markupsafe import Markup
from sqlalchemy import or_
from wtforms.validators import ValidationError

from grand_cedre.models.client import Client
from grand_cedre.models.contract import (
    Contract,
    FlatRateContract,
    ExchangeContract,
    RecurrentContract,
)
from grand_cedre.models.booking import Booking
from grand_cedre.models.invoice import Invoice
from grand_cedre.config import Config

current_dir = os.path.abspath(os.path.dirname(__file__))
output_dir = os.path.join(current_dir, "grand_cedre", "output")
template_dir = os.path.join(current_dir, "grand_cedre", "templates")
static_dir = os.path.join(current_dir, "grand_cedre", "static")

app = Flask("grand-cedre", template_folder=template_dir, static_folder=static_dir)
app.config.from_object(Config.from_env())
db = SQLAlchemy(app)
babel = Babel(app)


@babel.localeselector
def get_locale():
    return "fr"


def validate_start_end_dates(form, field):
    if form.start_date.data >= form.end_date.data:
        raise ValidationError("La date de début doit être antérieure à la date de fin")


class HomeAdminView(AdminIndexView):
    @expose("/")
    def admin_home(self):
        warning_messages = []
        clients_with_missing_details = (
            db.session.query(Client)
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
    app, name="grand-cedre", template_mode="bootstrap3", index_view=HomeAdminView()
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


class ContractView(GrandCedreView):
    column_exclude_list = ["type"]
    column_searchable_list = ("client.first_name", "client.last_name")

    column_labels = {
        "client": "Client",
        "start_date": "Date de début",
        "end_date": "Date de fin",
        "booking_price": "Prix par réservation",
        "hourly_rate": "Taux horaire",
        "total_hours": "Heures réservées",
        "remaining_hours": "Heures restantes",
    }
    form_excluded_columns = ["type"]
    form_args = {"start_date": {"validators": [validate_start_end_dates]}}

    def get_query(self):
        return self.session.query(self.model).filter_by(type="standard")


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

    def get_query(self):
        return (
            self.session.query(self.model)
            .join(Client)
            .filter(Client.is_owner.is_(False))
        )


class InvoiceView(GrandCedreView):
    def render_download_link(view, context, model, p):
        if model.is_valid:
            return Markup(
                f"<a href={url_for('download_invoice_as_pdf', invoice_id=model.id)}>💾</a>"
            )
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
    )
    column_labels = {
        "number": "# Facture",
        "client": "Client",
        "period": "Période",
        "total_price": "Total",
        "issued_at": "Date d'édition",
        "download": "Télécharger",
        "currency": "Devise",
    }
    column_formatters = {
        "client": (lambda v, c, m, p: f"{m.client}"),
        "total_price": (lambda v, c, m, p: f"{m.total_price}{m.symbol}"),
        "download": render_download_link,
    }


admin.add_view(ClientView(Client, db.session, "Clients"))
admin.add_view(ContractView(Contract, db.session, "Standards", category="Contrats"))
admin.add_view(
    ContractView(RecurrentContract, db.session, "Récurrents", category="Contrats")
)
admin.add_view(
    ContractView(ExchangeContract, db.session, "Échanges", category="Contrats")
)
admin.add_view(
    ContractView(FlatRateContract, db.session, "Forfait", category="Contrats")
)
admin.add_view(BookingView(Booking, db.session, "Réservations"))
admin.add_view(InvoiceView(Invoice, db.session, "Factures"))


@app.route("/")
def app_index():
    return redirect("/admin")


@app.route("/invoice/<int:invoice_id>/pdf")
def download_invoice_as_pdf(invoice_id):
    invoice = db.session.query(Invoice).get(invoice_id)
    if not invoice:
        abort(404)
    html = invoice.to_html()
    with tempfile.NamedTemporaryFile(
        dir=output_dir, suffix=".html", mode="w"
    ) as tmphtml:
        tmphtml.write(html)
        tmphtml.flush()
        pdf = HTML(tmphtml.name).write_pdf()
    response = make_response(pdf)
    response.headers["Content-type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={invoice.filename}"
    return response
