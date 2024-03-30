from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    SelectField,
    SubmitField,
    TextAreaField
)
from wtforms.validators import DataRequired

from plant_tracker.model import (
    MaintenanceType,
    ScheduledMaintenanceFrequencyType,
    TableScheduledMaintenanceLog
)
from plant_tracker.forms.helper import (
    apply_field_data_to_form,
    extract_form_data_to_obj,
    list_with_default,
    populate_form
)


scheduled_maintenance_attr_map = {
    'is_enabled': 'is_enabled',
    'maintenance_type': {
        'tbl_key': 'maintenance_type',
        'choices': MaintenanceType
    },
    'maintenance_frequency': {
        'tbl_key': 'maintenance_frequency',
        'choices': ScheduledMaintenanceFrequencyType
    },
    'maintenance_period_start': 'maintenance_period_start',
    'maintenance_period_end': 'maintenance_period_end',
    'notes': 'notes'
}


class AddScheduledMaintenanceForm(FlaskForm):
    """Add scheduled maintenance form"""

    is_enabled = BooleanField('Is Enabled', default=True)
    maintenance_type = SelectField(
        label='Maintenance Type',
        validators=[DataRequired()],
        choices=list_with_default(MaintenanceType),
        default=''
    )
    maintenance_period_start = DateField(
        label='Maintenance Period Start',
        validators=[DataRequired()],
        default=datetime.today,
        format='%Y-%m-%d'
    )
    maintenance_period_end = DateField(
        label='Maintenance Period End',
        validators=[DataRequired()],
        default=datetime.today,
        format='%Y-%m-%d'
    )
    maintenance_frequency = SelectField(
        label='Maintenance Frequency',
        validators=[DataRequired()],
        choices=list_with_default(ScheduledMaintenanceFrequencyType),
        default=''
    )
    notes = TextAreaField(label='Maintenance Notes')

    submit = SubmitField('Submit')


def populate_scheduled_maintenance_form(session, form: AddScheduledMaintenanceForm,
                                        maintenance_schedule_id: int = None) -> AddScheduledMaintenanceForm:
    """Handles compiling all form data for /add and /edit endpoints for scheduled_maintenance"""

    if maintenance_schedule_id is not None:
        schmaintlog: TableScheduledMaintenanceLog
        schmaintlog = session.query(TableScheduledMaintenanceLog).\
            filter(TableScheduledMaintenanceLog.maintenance_schedule_id == maintenance_schedule_id).one_or_none()
        if schmaintlog is None:
            return form

        form_field_map = apply_field_data_to_form(schmaintlog, scheduled_maintenance_attr_map)

        # Any cleanup of data should happen here...

        form = populate_form(form, form_field_map)

    return form


def get_scheduled_maintenance_data_from_form(session, form_data, maintenance_schedule_id: int = None) -> \
        TableScheduledMaintenanceLog:
    """Handles extracting all necessary form data for /add and /edit POST endpoints for family and places it in
        a new or existing table object"""

    if maintenance_schedule_id is not None:
        # Existing object -- replace data
        schmaintlog: TableScheduledMaintenanceLog
        schmaintlog = session.query(TableScheduledMaintenanceLog).\
            filter(TableScheduledMaintenanceLog.maintenance_schedule_id == maintenance_schedule_id).one_or_none()
    else:
        # New family object
        schmaintlog = TableScheduledMaintenanceLog()

    schmaintlog = extract_form_data_to_obj(form_data=form_data, table_obj=schmaintlog,
                                           obj_attr_map=scheduled_maintenance_attr_map, session=session)

    return schmaintlog
