from datetime import datetime

from flask_wtf import FlaskForm
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from wtforms import (
    DateField,
    IntegerField,
    MonthField,
    SelectField,
    SubmitField,
)
from wtforms.validators import DataRequired

from plant_tracker.model import (
    PlantSourceType,
    TablePlant,
    TablePlantSubRegion,
    TableSpecies
)
from plant_tracker.core.utils import default_if_prop_none
from plant_tracker.forms.helper import (
    DataListField,
    bool_with_unknown_list,
    list_with_default,
    populate_form
)


plant_attr_map = {
    'species': {
        'tbl_key': 'species.common_name',
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
    'planting_loc_x': 'planting_loc_x',
    'planting_loc_y': 'planting_loc_y'
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
        default=datetime.today().date(),
        format='%Y-%m-%d'
    )
    plant_source = SelectField(
        label='Plant Source',
        validators=[DataRequired()],
        choices=['None'] + [x for x in list(PlantSourceType)],
        default='None'
    )

    is_drip_irrigated = SelectField(label='Drip Irrigated?', choices=bool_with_unknown_list, default='unknown')
    is_in_container = SelectField(label='In Container?', choices=bool_with_unknown_list, default='unknown')

    planting_loc_x = IntegerField(
        label='Planting Location X'
    )
    planting_loc_y = IntegerField(
        label='Planting Location Y'
    )

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

        form_field_map = {}
        for attr, attr_details in plant_attr_map.items():
            if isinstance(attr_details, str):
                form_field_map[attr] = plant.__getattribute__(attr)
            elif isinstance(attr_details, dict):

                default_var = attr_details.get('empty_var', '')

                choices = None
                if 'choices' in attr_details.keys():
                    choices = attr_details['choices']
                elif attr == 'species':
                    choices = species_list

                form_field_map[attr] = {
                    'default': default_if_prop_none(plant, attr_details['tbl_key'], default=default_var),
                    'choices': list_with_default(choices, default=default_var)
                }
        # Any cleanup of data should happen here

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

    for attr, attr_details in plant_attr_map.items():
        attr_data = form_data[attr]
        if attr_data in bool_with_unknown_list:
            if attr_data == 'unknown':
                attr_data = None
            else:
                attr_data = attr_data == 'yes'
        elif attr_data == '':
            continue

        if isinstance(attr_details, dict):
            attr_table_obj_name = attr_details['tbl_key']
        else:
            attr_table_obj_name = attr_details
        if '.' in attr_table_obj_name:
            # nested value
            sub_obj_name, sub_obj_attr_name = attr_table_obj_name.split('.', maxsplit=1)
            sub_obj = plant.__getattribute__(sub_obj_name)
            if sub_obj is None or sub_obj.__getattribute__(sub_obj_attr_name) != attr_data:
                # Swap nested objects by querying for the new one
                # TODO: In order to unify this method with others, I need to confirm that
                #   I can grab the class for querying
                sub_obj = session.query(TableSpecies).filter(TableSpecies.scientific_name == attr_data).one_or_none()
                plant.__setattr__(sub_obj_name, sub_obj)
        else:
            plant.__setattr__(attr_table_obj_name, attr_data)

    # Handle x,y coordinate region determination
    if plant.planting_loc_x and plant.planting_loc_y:
        selected_region = None
        point = Point(plant.planting_loc_x, plant.planting_loc_y)
        sub_regions = session.query(TablePlantSubRegion).all()
        for sub_region in sub_regions:
            polygon_txt = sub_region.sub_region_poly
            polygon = Polygon([tuple(*x.split(',')) for x in polygon_txt.split(';')])
            if polygon.contains(point):
                selected_region = sub_region
                break
        plant.sub_region = selected_region

    return plant
