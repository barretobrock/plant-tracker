from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField
)
from wtforms.validators import DataRequired

from plant_tracker.model import TablePlantFamily
from plant_tracker.forms.helper import populate_form

# List of variables to extract between form & table object
family_objs = [
    'scientific_name',
    'common_name'
]


class AddFamilyForm(FlaskForm):
    """Add family form"""

    scientific_name = StringField(label='Scientific Name', validators=[DataRequired()])
    common_name = StringField(label='Common Name')

    submit = SubmitField('Submit')


def populate_family_form(session, form: AddFamilyForm, family_id: int = None) -> AddFamilyForm:
    """Handles compiling all form data for /add and /edit endpoints for family"""

    if family_id is not None:
        family: TablePlantFamily
        family = session.query(TablePlantFamily).filter(TablePlantFamily.plant_family_id == family_id).one_or_none()
        if family is None:
            return form
        form_field_map = {k: family.__getattribute__(k) for k in family_objs}
        # Any cleanup of data should happen here...

        form = populate_form(form, form_field_map)

    return form


def get_family_data_from_form(session, form_data, family_id: int = None) -> TablePlantFamily:
    """Handles extracting all necessary form data for /add and /edit POST endpoints for family and places it in
        a new or existing table object"""

    if family_id is not None:
        # Existing object -- replace data
        family: TablePlantFamily
        family = session.query(TablePlantFamily).filter(TablePlantFamily.plant_family_id == family_id).one_or_none()
    else:
        # New family object
        family = TablePlantFamily()

    for attr in family_objs:
        family.__setattr__(attr, form_data[attr])

    return family
