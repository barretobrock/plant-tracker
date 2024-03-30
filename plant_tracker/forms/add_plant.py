from datetime import datetime

from flask_wtf import FlaskForm
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from wtforms import (
    BooleanField,
    DateField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField
)
from wtforms.validators import DataRequired

from plant_tracker.model import (
    GeodataType,
    PlantSourceType,
    TableGeodata,
    TablePlant,
    TablePlantLocation,
    TableSpecies
)
from plant_tracker.forms.helper import (
    DataListField,
    apply_field_data_to_form,
    bool_with_unknown_list,
    extract_form_data_to_obj,
    list_with_default,
    populate_form
)


plant_attr_map = {
    'species': {
        'tbl_key': 'species.common_name',
        'sub_obj': TableSpecies
    },
    'plant_source': {
        'tbl_key': 'plant_source',
        'choices': PlantSourceType
    },
    'date_planted': 'date_planted',
    'is_drip_irrigated': {
        'tbl_key': 'is_drip_irrigated',
        'empty_var': 'unknown',
        'choices': bool_with_unknown_list
    },
    'is_in_container': {
        'tbl_key': 'is_in_container',
        'empty_var': 'unknown',
        'choices': bool_with_unknown_list
    },
    'is_dead': 'is_dead',
    'notes': 'notes'
}


class AddPlantForm(FlaskForm):
    """Add plant form"""

    species = DataListField(
        label='Species',
        validators=[DataRequired()],
    )
    date_planted = DateField(
        label='Planted Date',
        validators=[DataRequired()],
        default=datetime.today,
        format='%Y-%m-%d'
    )
    plant_source = SelectField(
        label='Plant Source',
        validators=[DataRequired()],
        choices=['None'] + [x for x in list(PlantSourceType)],
        default='None'
    )

    is_dead = BooleanField('Mark as dead', default=False)
    is_drip_irrigated = SelectField(label='Drip Irrigated?', choices=bool_with_unknown_list, default='unknown')
    is_in_container = SelectField(label='In Container?', choices=bool_with_unknown_list, default='unknown')

    shape_type = SelectField(label='Shape Type', choices=['polygon', 'point'], default='point')
    geodata = TextAreaField(label='GeoData')
    notes = TextAreaField(label='Notes')

    submit = SubmitField('Submit')


def populate_plant_form(session, form: AddPlantForm, plant_id: int = None) -> AddPlantForm:
    """Handles compiling all form data for /add and /edit endpoints for species"""
    species_list = [x.common_name for x in session.query(TableSpecies).order_by(TableSpecies.common_name).all()]

    form.species.datalist_entries = list_with_default(species_list)

    if plant_id is not None:
        plant: TablePlant
        plant = session.query(TablePlant).filter(TablePlant.plant_id == plant_id).one_or_none()
        if plant is None:
            return form

        plant_attr_map['species']['choices'] = species_list

        form_field_map = apply_field_data_to_form(plant, plant_attr_map)

        # Any cleanup of data should happen here
        if plant.plant_location:
            form['geodata'].data = plant.plant_location.geodata.data
            form['shape_type'].data = 'polygon' if plant.plant_location.geodata.is_polygon else 'point'

        form = populate_form(form, form_field_map)
    return form


def get_plant_data_from_form(session, form_data, plant_id: int = None) -> TablePlant:
    """Handles extracting all necessary form data for /add and /edit POST endpoints for plant and places it in
        a new or existing table object"""

    if plant_id is not None:
        # Existing object -- replace data
        plant: TablePlant
        plant = session.query(TablePlant).filter(TablePlant.plant_id == plant_id).one_or_none()
    else:
        # New plant object
        plant = TablePlant()

    plant = extract_form_data_to_obj(form_data=form_data, table_obj=plant,
                                     obj_attr_map=plant_attr_map, session=session)
    return plant
