This project implements tools used in the administration of [Le Grand Cèdre](https://sophrologie-chalon.com/le-grand-cedre/), a flexible working space welcoming alternative medicine practitioners, in the form of a web interface.

It allows to register clients base, import booking information from Google Calendars, define pricings, edit contracts, track expenses, generate invoices, monthly, quarterly and yearly balance sheets, upload documents to Google Drive, etc.

It was not designed as a generic tool, but rather an implementation of specific needs. The code was nevertheless made open-source for the sake of transparency.

## Operations

### Import pricings

When the app is running for the first time, run the following command to import the different pricings in database:

```console
% flask import-fixtures
```

### Import bookings

The bookings can regularly be imported from Google Calendar in an idempotent way by running

```console
% flask import-bookings
```

### Generate invoices

Invoices for the previous month (by default, which can be override with the `--year` and `--month` arguments) can be generated and uploaded to Google Drive by running

```console
% flask generate-invoices
```

If the `--no-commit` flag is provided, the calendar events will be imported but nothing will be committed to the database. If the `--no-upload` flag is passed, the invoices will not be uploaded to Google Drive.


### Create a balance sheet

A balance sheet (CSV file listing all paid invoices for the given period and all expenses) for the previous month (by default, which can be override with the `--year` and `--month` arguments) can be generated and uploaded to Google Drive by running

```console
% flask create-balance-sheet
```

If the `--no-upload` flag is passed, the balance sheet will not be uploaded to Google Drive.
