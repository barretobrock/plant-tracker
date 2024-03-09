from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField
)

from plant_tracker.model import TableAlternateNames
from plant_tracker.forms.helper import (
    apply_field_data_to_form,
    extract_form_data_to_obj,
    populate_form
)


name_attr_map = {
    'name': 'name',
    'is_scientific': 'is_scientific'
}


class AddNameForm(FlaskForm):
    """Add name form"""

    common_name = StringField(label='Common Name')
    scientific_name = StringField(label='Scientific Name')

    submit = SubmitField('Submit')


def populate_name_form(session, form: AddNameForm, alternate_name_id: int = None) -> AddNameForm:
    """Handles compiling all form data for /add and /edit endpoints for alt_name"""

    if alternate_name_id is not None:
        altname: TableAlternateNames
        altname = session.query(TableAlternateNames).\
            filter(TableAlternateNames.alternate_name_id == alternate_name_id).one_or_none()
        if altname is None:
            return form

        if altname.is_scientific:
            form_field_map = {'scientific_name': altname.name}
        else:
            form_field_map = {'common_name': altname.name}

        # Any cleanup of data should happen here...

        form = populate_form(form, form_field_map)

    return form


def get_name_data_from_form(session, form_data, alternate_name_id: int = None) -> TableAlternateNames:
    """Handles extracting all necessary form data for /add and /edit POST endpoints for family and places it in
        a new or existing table object"""

    if alternate_name_id is not None:
        # Existing object -- replace data
        altname: TableAlternateNames
        altname = session.query(TableAlternateNames).\
            filter(TableAlternateNames.alternate_name_id == alternate_name_id).one_or_none()
    else:
        # New family object
        altname = TableAlternateNames()

    if form_data['scientific_name']:
        altname.is_scientific = True
        altname.name = form_data['scientific_name']
    else:
        altname.is_scientific = False
        altname.name = form_data['common_name']

    return altname
