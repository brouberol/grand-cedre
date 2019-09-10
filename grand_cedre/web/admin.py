from flask import url_for, flash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.fields import Select2Field
from flask_admin.model.form import converts
from flask_admin.contrib.sqla.form import AdminModelConverter
from markupsafe import Markup, escape
from wtforms.validators import ValidationError, Email, DataRequired
from sqlalchemy import or_, func
from datetime import date
from sqlalchemy.sql.sqltypes import Enum as SQLEnum

from . import app
from .db import db

from grand_cedre.models.booking import DailyBooking
from grand_cedre.models.client import Client
from grand_cedre.models.invoice import Invoice
from grand_cedre.models.room import Room
from grand_cedre.models.contract import Contract
from grand_cedre.models.pricing import (
    Pricing,
    CollectiveRoomRegularPricing,
    CollectiveRoomOccasionalPricing,
    FlatRatePricing,
    RecurringPricing,
)
from grand_cedre.models.types import RoomTypeEnum, ContractTypeEnum, ContractType
from grand_cedre.models.balance import BalanceSheet
from grand_cedre.models.expense import Expense


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

        choices = [(v._name_, escape(v._value_)) for v in kwargs.pop("model", [])]
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


def validate_check_or_wire_payment_method(form, field):
    if form.check_number.data and form.wire_transfer_number.data:
        raise ValidationError(
            "Une facture ne peut pas être payée par chèque *et* virement"
        )


class GrandCedreView(ModelView):
    list_template = "admin/model_list.html"
    model_form_converter = CustomAdminConverter

    def search_placeholder(self):
        return "Recherche"


class ClientView(GrandCedreView):
    can_delete = False
    column_exclude_list = ["is_owner"]
    column_searchable_list = ("first_name", "last_name", "email")
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


class _ContractView(GrandCedreView):
    @classmethod
    def get_type(cls):
        return cls._type

    def get_count_query(self):
        return (
            self.session.query(func.count("*"))
            .select_from(self.model)
            .filter_by(type=self.get_type())
        )


class ContractView(_ContractView):
    def format_room_type(v, c, m, p):
        if not m.room_type:
            return ""
        elif m.room_type not in RoomTypeEnum:
            return ""
        return f"{RoomTypeEnum[m.room_type._name_]._value_}"

    _type = ContractType.standard
    can_delete = False
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
        "flat_rate_pricing": "Taux horaire",
        "weekly_hours": "Nombre d'heures hebdomadaires",
    }
    column_list = ["type", "client", "room_type", "start_date", "end_date"]
    column_formatters = {
        "room_type": format_room_type,
        "type": (lambda v, c, m, p: f"{ContractTypeEnum[m.type]._value_}"),
    }
    form_excluded_columns = [
        "type",
        "invoices",
        "total_hours",
        "remaining_hours",
        "flat_rate_pricing",
        "recurring_pricing",
        "end_date",
        "weekly_hours",
    ]
    form_args = {
        "start_date": {"validators": [validate_start_end_dates], "default": date.today},
        "room_type": {"model": RoomTypeEnum},
        "type": {"default": _ContractView.get_type},
        "weekly_hours": {"validators": [DataRequired()]},
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.type = self.get_type()

    def get_query(self):
        return self.session.query(self.model).filter(self.model.type == self._type)


class OneShotContractView(ContractView):
    _type = ContractType.one_shot


class ExchangeContractView(ContractView):
    _type = ContractType.exchange


class RecurringContractView(ContractView):
    _type = ContractType.recurring

    column_list = [
        "type",
        "client",
        "room_type",
        "weekly_hours",
        "start_date",
        "end_date",
    ]
    form_excluded_columns = [
        "type",
        "invoices",
        "end_date",
        "flat_rate_pricing",
        "recurring_pricing",
        "total_hours",
        "remaining_hours",
    ]

    def on_model_change(self, form, model, is_created):
        super().on_model_change(form, model, is_created)
        recurring_pricing = (
            db.session.query(RecurringPricing)
            .filter(RecurringPricing.duration_from < model.weekly_hours)
            .filter(RecurringPricing.duration_to >= model.weekly_hours)
            .filter(RecurringPricing.valid_from <= model.start_date)
            .filter(
                or_(
                    RecurringPricing.valid_to >= date.today(),
                    RecurringPricing.valid_to.is_(None),
                )
            )
            .first()
        )
        model.recurring_pricing = recurring_pricing


class FlatRateContractView(ContractView):
    _type = ContractType.flat_rate

    column_list = [
        "type",
        "client",
        "room_type",
        "start_date",
        "end_date",
        "flat_rate_pricing",
        "total_hours",
        "remaining_hours",
    ]
    form_excluded_columns = [
        "type",
        "invoices",
        "recurring_pricing",
        "weekly_hours",
        "room_type",
    ]
    form_args = {
        "total_hours": {"validators": [DataRequired()]},
        "remaining_hours": {"validators": [DataRequired()]},
        "room_type": {"model": RoomTypeEnum},
    }

    def on_model_change(self, form, model, is_created):
        super().on_model_change(form, model, is_created)
        model.room_type = RoomTypeEnum.individual


class BookingView(GrandCedreView):
    column_default_sort = ("date", True)
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
            lambda v, c, m, p: f"{RoomTypeEnum[m.contract.room_type._name_]._value_}"
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

    def render_price(view, context, model, p):
        return f"{model.total_price}{model.symbol}"

    @action(
        "mark_as_payed",
        "Marquer comme payées",
        "Êtes vous sûr(e) de vouloir marquer ces factures comme payées?",
    )
    def action_mark_as_payed(self, ids):
        today = date.today()
        invoices = self.session.query(Invoice).filter(Invoice.id.in_(ids))
        for invoice in invoices:
            invoice.payed_at = today
            self.session.add(invoice)

        self.session.commit()
        flash(f"Les factures ont été marquées comme payées le {today}")

    column_default_sort = (Invoice.issued_at, True)
    can_delete = False
    column_searchable_list = ("contract.client.first_name", "contract.client.last_name")
    column_list = (
        "number",
        "contract",
        "client",
        Invoice.period,
        "price",
        Invoice.issued_at,
        "payed_at",
        "check_number",
        "wire_transfer_number",
        "download",
        "send",
    )
    column_labels = {
        "number": "# Facture",
        "client": "Client",
        "period": "Période",
        "price": "Total",
        "issued_at": "Date d'édition",
        "download": "Télécharger",
        "currency": "Devise",
        "send": "Envoyer",
        "daily_bookings": "Réservations",
        "contract": "Contrats",
        "payed_at": "Date d'encaissement",
        "check_number": "# Chèque",
        "wire_transfer_number": "# Virement",
    }
    column_formatters = {
        "client": (lambda v, c, m, p: f"{m.contract.client}"),
        "price": render_price,
        "download": render_download_link,
        "send": render_send_link,
    }
    form_args = {
        "issued_at": {"default": date.today},
        "check_number": {"validators": [validate_check_or_wire_payment_method]},
        "wire_transfer_number": {"validators": [validate_check_or_wire_payment_method]},
    }
    form_excluded_columns = ["period"]


class RoomView(GrandCedreView):
    can_edit = False
    can_delete = False
    column_labels = {
        "name": "Nom",
        "individual": "Individuelle?",
        "calendar_id": "ID du Google Agenda",
    }


class BasePricingView(GrandCedreView):
    can_edit = False
    can_delete = False


class PricingView(BasePricingView):
    def format_duration(view, context, model, p):
        if model.duration_to is None:
            return f"]{model.duration_from},∞["
        return f"]{model.duration_from}, {model.duration_to}]"

    column_labels = {
        "valid_from": "Date d'instauration",
        "valid_to": "Date de fin de validité",
        "hourly_price": "Prix à l'heure",
        "duration_from": "Durée minimale (exclue)",
        "duration_to": "Durée maximale (inclue)",
    }
    column_list = ["duration", "hourly_price", "valid_from", "valid_to"]
    column_formatters = {"duration": format_duration}
    form_excluded_columns = ["type"]


class RecurringPricingView(BasePricingView):
    column_labels = {
        "valid_from": "Date d'instauration",
        "valid_to": "Date de fin de validité",
        "monthly_price": "Prix au mois",
        "duration_from": "Durée minimale (exclue)",
        "duration_to": "Durée maximal (inclue)",
    }
    column_list = ["duration", "monthly_price", "valid_from", "valid_to"]
    column_formatters = {"duration": (lambda v, c, m, p: f"{m.format_interval()}")}
    form_excluded_columns = ["type"]


class FlatRatePricingView(BasePricingView):
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

        recurring_contracts_with_missing_details = (
            db.session.query(Contract)
            .filter(Contract.type == ContractType.recurring)
            .filter(Contract.weekly_hours.is_(None))
        ).all()
        if recurring_contracts_with_missing_details:
            warning_messages.append(
                (
                    "Certains contrats d'occupation récurrente n'ont pas d'heures "
                    "hebdomadaires renseignéees, ce qui bloquera la génération "
                    "de facture"
                )
            )
        return self.render("admin/home.html", warning_messages=warning_messages)


class BalanceSheetView(GrandCedreView):
    def render_download_link(view, context, model, p):
        return Markup(
            f"<a href={url_for('download_balance_sheet_as_csv', balance_id=model.id)}>💾</a>"
        )

    column_list = ["start_date", "end_date", "download_link"]
    column_labels = {
        "start_date": "Date de début",
        "end_date": "Date de fin",
        "download_link": "Télécharger",
    }
    column_formatters = {"download_link": render_download_link}


class ExpenseModel(GrandCedreView):
    column_default_sort = ("date", True)
    column_labels = {"date": "Date", "label": "Motif", "price": "Montant"}


admin = Admin(
    app, name="grand-cedre", template_mode="bootstrap3", index_view=HomeAdminView()
)

admin.add_view(ClientView(Client, db.session, "Clients"))
admin.add_view(ContractView(Contract, db.session, "Standards", category="Contrats"))
admin.add_view(
    OneShotContractView(
        Contract,
        db.session,
        "Réservations occasionelles",
        category="Contrats",
        endpoint="one_shot_contracts",
    )
)
admin.add_view(
    ExchangeContractView(
        Contract,
        db.session,
        "Échanges",
        category="Contrats",
        endpoint="exchange_contracts",
    )
)
admin.add_view(
    FlatRateContractView(
        Contract,
        db.session,
        "Forfait",
        category="Contrats",
        endpoint="flat_rate_contracts",
    )
)
admin.add_view(
    RecurringContractView(
        Contract,
        db.session,
        "Occupation récurrente",
        category="Contrats",
        endpoint="recurring_contracts",
    )
)
admin.add_view(BookingView(DailyBooking, db.session, "Réservations"))
admin.add_view(InvoiceView(Invoice, db.session, "Factures"))
admin.add_view(ExpenseModel(Expense, db.session, "Dépenses"))
admin.add_view(BalanceSheetView(BalanceSheet, db.session, "Bilans"))
admin.add_view(RoomView(Room, db.session, "Salles"))
admin.add_view(
    PricingView(
        Pricing,
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
admin.add_view(
    FlatRatePricingView(FlatRatePricing, db.session, "Forfait", category="Tarifs")
)
