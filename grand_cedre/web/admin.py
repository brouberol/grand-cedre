from flask import url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.fields import Select2Field
from flask_admin.model.form import converts
from flask_admin.contrib.sqla.form import AdminModelConverter
from markupsafe import Markup, escape
from wtforms.validators import ValidationError, Email
from sqlalchemy import or_
from datetime import date
from sqlalchemy.sql.sqltypes import Enum as SQLEnum

from . import app
from .db import db

from grand_cedre.models.booking import DailyBooking
from grand_cedre.models.client import Client
from grand_cedre.models.invoice import Invoice
from grand_cedre.models.room import Room
from grand_cedre.models.contract import (
    Contract,
    FlatRateContract,
    ExchangeContract,
    OneShotContract,
    RecurringContract,
    RoomType,
    ContractTypeEnum,
)
from grand_cedre.models.pricing import (
    IndividualRoomModularPricing,
    CollectiveRoomRegularPricing,
    CollectiveRoomOccasionalPricing,
    FlatRatePricing,
    RecurringPricing,
)


class EnumField(Select2Field):
    def __init__(self, column, **kwargs):
        assert isinstance(column.type, SQLEnum)

        def coercer(value):
            # coerce incoming value into an enum value
            if isinstance(value, column.type.enum_class):
                return value
            elif isinstance(value, str):
                return column.type.enum_class[value]
            else:
                assert False

        choices = [(v._name_, escape(v._value_)) for v in kwargs.pop("model")]
        super(EnumField, self).__init__(coerce=coercer, choices=choices, **kwargs)

    def pre_validate(self, form):
        # we need to override the default SelectField validation because it
        # apparently tries to directly compare the field value with the choice
        # key; it is not clear how that could ever work in cases where the
        # values and choice keys must be different types

        for (v, _) in self.choices:
            if self.data == self.coerce(v):
                break
        else:
            raise ValueError(self.gettext("Not a valid choice"))


class CustomAdminConverter(AdminModelConverter):
    @converts("sqlalchemy.sql.sqltypes.Enum")
    def conv_enum(self, field_args, **extra):
        return EnumField(column=extra["column"], **field_args)


def validate_start_end_dates(form, field):
    if hasattr(form, "end_date"):
        if form.start_date.data >= form.end_date.data:
            raise ValidationError(
                "La date de début doit être antérieure à la date de fin"
            )


class GrandCedreView(ModelView):
    model_form_converter = CustomAdminConverter

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
    form_excluded_columns = ["is_owner", "contracts", "daily_bookings", "invoices"]
    form_args = {"email": {"validators": [Email()]}}


class ContractView(GrandCedreView):
    def format_room_type(v, c, m, p):
        if not m.room_type:
            return ""
        elif m.room_type not in RoomType:
            return ""
        return f"{RoomType[m.room_type._name_]._value_}"

    column_searchable_list = ("client.first_name", "client.last_name")
    column_labels = {
        "client": "Client",
        "start_date": "Date de début",
        "end_date": "Date de fin",
        "booking_price": "Prix par réservation",
        "hourly_rate": "Taux horaire",
        "total_hours": "Heures réservées",
        "remaining_hours": "Heures restantes",
        "room_type": "Type de salle",
        "type": "Type de contrat",
        "total_hours": "Heures prépayées",
        "remaining_hours": "Heures restantes",
    }
    form_excluded_columns = ["type"]
    form_args = {
        "start_date": {"validators": [validate_start_end_dates], "default": date.today},
        "room_type": {"model": RoomType},
    }
    column_formatters = {
        "room_type": format_room_type,
        "type": (lambda v, c, m, p: f"{ContractTypeEnum[m.type]._value_}"),
    }

    def get_query(self):

        return self.session.query(self.model).filter(
            self.model.type == self.model._type
        )


class BookingView(GrandCedreView):
    column_labels = {
        "client": "Client",
        "date": "Date",
        "price": "Prix",
        "duration_hours": "Durée (h)",
        "individual": "Salle individelle?",
        "room_type": "Type de salle",
        "contract_type": "Type de contrat",
    }
    column_list = [
        "contract_type",
        "room_type",
        "client",
        "date",
        "duration_hours",
        "price",
    ]
    column_filters = ["price"]
    column_searchable_list = ("client.first_name", "client.last_name", "date")
    form_excluded_columns = ("frozen", "invoice")
    column_formatters = {
        "room_type": (
            lambda v, c, m, p: f"{RoomType[m.contract.room_type._name_]._value_}"
        ),
        "contract_type": (
            lambda v, c, m, p: f"{ContractTypeEnum[m.contract.type]._value_}"
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
        "daily_bookings": "Réservations",
    }
    column_formatters = {
        "client": (lambda v, c, m, p: f"{m.client}"),
        "total_price": (lambda v, c, m, p: f"{m.total_price}{m.symbol}"),
        "download": render_download_link,
        "send": render_send_link,
    }
    form_args = {"issued_at": {"default": date.today}}


class RoomView(GrandCedreView):
    column_labels = {
        "name": "Nom",
        "individual": "Individuelle?",
        "calendar_id": "ID du Google Agenda",
    }


class PricingView(GrandCedreView):
    def format_duration(view, context, model, p):
        if model.duration_to is None:
            return f"]{model.duration_from},∞["
        return f"]{model.duration_from}, {model.duration_to}]"

    column_labels = {
        "valid_from": "Date d'instauration",
        "valid_to": "Date de fin de validité",
        "hourly_price": "Prix à l'heure",
        "duration_from": "Durée minimale (exclue)",
        "duration_to": "Durée maximal (inclue)",
    }
    column_list = ["duration", "hourly_price", "valid_from", "valid_to"]
    column_formatters = {"duration": format_duration}
    form_excluded_columns = ["type"]


class RecurringPricingView(GrandCedreView):
    def format_duration(view, context, model, p):
        return f"] {model.duration_from / 8}j, {model.duration_to / 8}j ]"

    column_labels = {
        "valid_from": "Date d'instauration",
        "valid_to": "Date de fin de validité",
        "monthly_price": "Prix au mois",
        "duration_from": "Durée minimale (exclue)",
        "duration_to": "Durée maximal (inclue)",
    }
    column_list = ["duration", "monthly_price", "valid_from", "valid_to"]
    column_formatters = {"duration": format_duration}
    form_excluded_columns = ["type"]


class FlatRateView(GrandCedreView):
    column_labels = {
        "flat_rate": "Prix à l'heure",
        "prepaid_hours": "Heures prépayées",
        "valid_from": "Date d'instauration",
        "valid_to": "Date de fin de validité",
        "duration_from": "Durée minimale (exclue)",
        "duration_to": "Durée maximal (inclue)",
    }
    column_list = ["prepaid_hours", "flat_rate", "valid_from", "valid_to"]
    form_excluded_columns = ["type"]


class HomeAdminView(AdminIndexView):
    @expose("/")
    def admin_home(self):
        # detect flat rate contracts closing to expiry
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
admin.add_view(
    ContractView(
        RecurringContract, db.session, "Occupation récurrente", category="Contrats"
    )
)
admin.add_view(BookingView(DailyBooking, db.session, "Réservations"))
admin.add_view(InvoiceView(Invoice, db.session, "Factures"))
admin.add_view(RoomView(Room, db.session, "Salles"))
admin.add_view(
    PricingView(
        IndividualRoomModularPricing,
        db.session,
        "Salle individelle - Occupation modulaire",
        category="Tarifs",
    )
)
admin.add_view(
    RecurringPricingView(
        RecurringPricing,
        db.session,
        "Salle individelle - Occupation récurrente",
        category="Tarifs",
    )
)

admin.add_view(
    PricingView(
        CollectiveRoomRegularPricing,
        db.session,
        "Salle collective - Occupation regulière",
        category="Tarifs",
    )
)
admin.add_view(
    PricingView(
        CollectiveRoomOccasionalPricing,
        db.session,
        "Salle collective - Occupation occasionelle",
        category="Tarifs",
    )
)
admin.add_view(FlatRateView(FlatRatePricing, db.session, "Forfait", category="Tarifs"))
