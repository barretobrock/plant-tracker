from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    IntegerField,
    RadioField,
    SelectField,
    SubmitField,
    TextAreaField
)
from wtforms.validators import DataRequired

from plant_tracker.model import (
    ObservationType,
    TableObservationLog
)
from plant_tracker.forms.helper import (
    apply_field_data_to_form,
    extract_form_data_to_obj,
    list_with_default,
    populate_form
)


observation_attr_map = {
    'plant_height_mm': 'plant_height_mm',
    'plant_width_mm': 'plant_width_mm',
    'observation_type': {
        'tbl_key': 'observation_type',
        'choices': ObservationType
    },
    'observation_date': 'observation_date',
    'notes': 'notes'
}


class AddObservationForm(FlaskForm):
    """Add observation form"""

    observation_type = SelectField(
        label='Observation Type',
        validators=[DataRequired()],
        choices=list_with_default(ObservationType),
        default=''
    )
    observation_date = DateField(
        label='Observation Date',
        validators=[DataRequired()],
        default=datetime.today,
        format='%Y-%m-%d'
    )
    plant_rating = RadioField(
        label='Plant Rating',
        choices=[
            '1 - Poor',
            '2 - Not Great',
            '3 - Average',
            '4 - Good',
            '5 - Excellent',
        ]
    )
    plant_height_mm = IntegerField(label='Plant Height mm')
    plant_width_mm = IntegerField(label='Plant Width mm')
    notes = TextAreaField(label='Observation Notes')

    submit = SubmitField('Submit')


def populate_observation_form(session, form: AddObservationForm,
                              observation_log_id: int = None) -> AddObservationForm:
    """Handles compiling all form data for /add and /edit endpoints for observation"""

    if observation_log_id is not None:
        obslog: TableObservationLog
        obslog = session.query(TableObservationLog).\
            filter(TableObservationLog.observation_log_id == observation_log_id).one_or_none()
        if obslog is None:
            return form

        form_field_map = apply_field_data_to_form(obslog, observation_attr_map)

        # Any cleanup of data should happen here...

        form = populate_form(form, form_field_map)

    return form


def get_observation_data_from_form(session, form_data, observation_log_id: int = None) -> \
        TableObservationLog:
    """Handles extracting all necessary form data for /add and /edit POST endpoints for family and places it in
        a new or existing table object"""

    if observation_log_id is not None:
        # Existing object -- replace data
        obslog: TableObservationLog
        obslog = session.query(TableObservationLog).\
            filter(TableObservationLog.observation_log_id == observation_log_id).one_or_none()
    else:
        # New object
        obslog = TableObservationLog()

    obslog = extract_form_data_to_obj(form_data=form_data, table_obj=obslog,
                                      obj_attr_map=observation_attr_map, session=session)
    if form_data['plant_rating']:
        try:
            obslog.plant_rating = int(form_data['plant_rating'].strip(' ')[0])
        except Exception:
            pass
    return obslog
