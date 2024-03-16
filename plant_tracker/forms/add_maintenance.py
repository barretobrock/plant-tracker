from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    SelectField,
    SubmitField,
    TextAreaField
)
from wtforms.validators import DataRequired

from plant_tracker.model import (
    MaintenanceType,
    TableMaintenanceLog
)
from plant_tracker.forms.helper import (
    apply_field_data_to_form,
    extract_form_data_to_obj,
    list_with_default,
    populate_form
)


maintenance_attr_map = {
    'maintenance_type': {
        'tbl_key': 'maintenance_type',
        'choices': MaintenanceType
    },
    'maintenance_date': 'maintenance_date',
    'notes': 'notes'
}


class AddMaintenanceForm(FlaskForm):
    """Add maintenance form"""

    maintenance_type = SelectField(
        label='Maintenance Type',
        validators=[DataRequired()],
        choices=list_with_default(MaintenanceType),
        default=''
    )
    maintenance_date = DateField(
        label='Maintenance Date',
        validators=[DataRequired()],
        default=datetime.today().date(),
        format='%Y-%m-%d'
    )
    notes = TextAreaField(label='Maintenance Notes')

    submit = SubmitField('Submit')


def populate_maintenance_form(session, form: AddMaintenanceForm,
                              maintenance_log_id: int = None) -> AddMaintenanceForm:
    """Handles compiling all form data for /add and /edit endpoints for scheduled_maintenance"""

    if maintenance_log_id is not None:
        maintlog: TableMaintenanceLog
        maintlog = session.query(TableMaintenanceLog).\
            filter(TableMaintenanceLog.maintenance_log_id == maintenance_log_id).one_or_none()
        if maintlog is None:
            return form

        form_field_map = apply_field_data_to_form(maintlog, maintenance_attr_map)

        # Any cleanup of data should happen here...

        form = populate_form(form, form_field_map)

    return form


def get_maintenance_data_from_form(session, form_data, maintenance_log_id: int = None) -> \
        TableMaintenanceLog:
    """Handles extracting all necessary form data for /add and /edit POST endpoints for family and places it in
        a new or existing table object"""

    if maintenance_log_id is not None:
        # Existing object -- replace data
        maintlog: TableMaintenanceLog
        maintlog = session.query(TableMaintenanceLog).\
            filter(TableMaintenanceLog.maintenance_log_id == maintenance_log_id).one_or_none()
    else:
        # New object
        maintlog = TableMaintenanceLog()

    maintlog = extract_form_data_to_obj(form_data=form_data, table_obj=maintlog,
                                        obj_attr_map=maintenance_attr_map, session=session)

    return maintlog
