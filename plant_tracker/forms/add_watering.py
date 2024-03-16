from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    SubmitField,
    TextAreaField
)
from wtforms.validators import DataRequired

from plant_tracker.model import (
    TableWateringLog
)
from plant_tracker.forms.helper import (
    apply_field_data_to_form,
    extract_form_data_to_obj,
    populate_form
)


watering_attr_map = {
    'watering_date': 'watering_date',
    'notes': 'notes'
}


class AddWateringForm(FlaskForm):
    """Add watering form"""
    watering_date = DateField(
        label='Watering Date',
        validators=[DataRequired()],
        default=datetime.today().date(),
        format='%Y-%m-%d'
    )
    notes = TextAreaField(label='Watering Notes')

    submit = SubmitField('Submit')


def populate_watering_form(session, form: AddWateringForm, watering_log_id: int = None) -> AddWateringForm:
    """Handles compiling all form data for /add and /edit endpoints for watering"""

    if watering_log_id is not None:
        waterlog: TableWateringLog
        waterlog = session.query(TableWateringLog).\
            filter(TableWateringLog.watering_log_id == watering_log_id).one_or_none()
        if waterlog is None:
            return form

        form_field_map = apply_field_data_to_form(waterlog, watering_attr_map)

        # Any cleanup of data should happen here...

        form = populate_form(form, form_field_map)

    return form


def get_watering_data_from_form(session, form_data, watering_log_id: int = None) -> \
        TableWateringLog:
    """Handles extracting all necessary form data for /add and /edit POST endpoints for family and places it in
        a new or existing table object"""

    if watering_log_id is not None:
        # Existing object -- replace data
        waterlog: TableWateringLog
        waterlog = session.query(TableWateringLog).\
            filter(TableWateringLog.watering_log_id == watering_log_id).one_or_none()
    else:
        # New object
        waterlog = TableWateringLog()

    waterlog = extract_form_data_to_obj(form_data=form_data, table_obj=waterlog,
                                        obj_attr_map=watering_attr_map, session=session)
    return waterlog
