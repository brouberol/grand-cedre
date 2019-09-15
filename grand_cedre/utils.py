import datetime
import calendar
import googleapiclient.http
import logging

logger = logging.getLogger("grand-cedre")


def utcnow():
    return datetime.datetime.utcnow()


def start_of_month(year=None, month=None):
    if year and month:
        return datetime.datetime(year, month, 1, 0, 0, 0)

    now = utcnow()
    monthstart = now.replace(day=1, hour=0, minute=0, second=0)
    return monthstart


def end_of_month(year=None, month=None):
    if year and month:
        day = datetime.datetime(year, month, 1, 0, 0, 0)
    else:
        day = utcnow()
    _, last_day = calendar.monthrange(day.year, day.month)
    monthend = day.replace(day=last_day, hour=0, minute=0, second=0)
    return monthend


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items())
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True


def ensure_drive_folder(name, parent_id, drive_service):
    """Create a Drive folder located in argument parent if not already exists.

    Return the folder id.

    """
    preexisting_folder = (
        drive_service.files()
        .list(q=f"name = '{name}' and trashed = false and '{parent_id}' in parents")
        .execute()
    )
    if preexisting_folder["files"]:
        logger.debug(f"Drive folder {name} already exists")
        return preexisting_folder["files"][0]["id"]
    else:
        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        logger.info(f"Creating Drive folder {name}")
        file = drive_service.files().create(body=file_metadata, fields="id").execute()
        return file["id"]


def ensure_drive_file(
    local_filename, remote_filename, description, mimetype, parent_id, drive_service
):
    """Upload a file the to argument parent Drive id, and overrite if it already exists."""
    media_body = googleapiclient.http.MediaFileUpload(local_filename, mimetype=mimetype)
    preexisting_file = (
        drive_service.files()
        .list(
            q=(
                f"name = '{remote_filename}' "
                f"and trashed = false "
                f"and '{parent_id}' in parents "
                f"and mimeType = '{mimetype}'"
            )
        )
        .execute()
    )
    if preexisting_file["files"]:
        logger.debug(f"File {remote_filename} already exists. Overwriting.")
        drive_service.files().update(
            media_body=media_body, fileId=preexisting_file["files"][0]["id"]
        ).execute()
    else:
        logger.info(f"Creating file {remote_filename}")
        body = {
            "name": remote_filename,
            "description": description,
            "mime_type": mimetype,
            "parents": [parent_id],
        }
        drive_service.files().create(body=body, media_body=media_body).execute()
