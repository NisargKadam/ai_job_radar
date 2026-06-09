from app.db.models import SettingsRow
from app.db.session import SessionLocal
from app.schemas import SettingsIn, SettingsOut


def _row(session) -> SettingsRow:
    row = session.query(SettingsRow).first()
    if row is None:
        row = SettingsRow()
        session.add(row)
        session.commit()
    return row


def get_settings() -> SettingsOut:
    with SessionLocal() as s:
        return SettingsOut.model_validate(_row(s))


def get_settings_dict() -> dict:
    return get_settings().model_dump()


def update_settings(patch: SettingsIn) -> SettingsOut:
    with SessionLocal() as s:
        row = _row(s)
        for field, value in patch.model_dump(exclude_none=True).items():
            setattr(row, field, value)
        s.commit()
        return SettingsOut.model_validate(row)
