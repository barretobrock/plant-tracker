from flask_wtf import FlaskForm
from wtforms import (
    SelectField,
    StringField,
    SubmitField,
    TextAreaField
)
from wtforms.validators import DataRequired

from plant_tracker.model import (
    DurationType,
    LeafRetentionType,
    LightRequirementType,
    SoilMoistureType,
    TablePlantFamily,
    TablePlantHabit,
    TableSpecies,
    WaterRequirementType
)
from plant_tracker.forms.helper import (
    DataListField,
    apply_field_data_to_form,
    bool_with_unknown_list,
    extract_form_data_to_obj,
    list_with_default,
    populate_form
)

species_attr_map = {
    'common_name': 'common_name',
    'genus': 'genus',
    'species': 'species',
    'family': {
        'tbl_key': 'plant_family.scientific_name',
        'sub_obj': TablePlantFamily
    },
    'habit': {
        'tbl_key': 'habit.plant_habit',
        'sub_obj': TablePlantHabit
    },
    'duration': {
        'tbl_key': 'duration',
        'choices': DurationType
    },
    'is_native': {
        'tbl_key': 'is_native',
        'empty_var': 'unknown',
        'choices': bool_with_unknown_list
    },
    'is_drought_tolerant': {
        'tbl_key': 'is_drought_tolerant',
        'empty_var': 'unknown',
        'choices': bool_with_unknown_list
    },
    'is_heat_tolerant': {
        'tbl_key': 'is_heat_tolerant',
        'empty_var': 'unknown',
        'choices': bool_with_unknown_list
    },
    'is_freeze_tolerant': {
        'tbl_key': 'is_freeze_tolerant',
        'empty_var': 'unknown',
        'choices': bool_with_unknown_list
    },
    'water_requirement': {
        'tbl_key': 'water_requirement',
        'choices': WaterRequirementType
    },
    'light_requirement': {
        'tbl_key': 'light_requirement',
        'choices': LightRequirementType
    },
    'soil_moisture': {
        'tbl_key': 'soil_moisture',
        'choices': SoilMoistureType
    },
    'leaf_retention': {
        'tbl_key': 'leaf_retention',
        'choices': LeafRetentionType
    },
    'usda_symbol': 'usda_symbol',
    'bloom_start_month': {
        'tbl_key': 'bloom_start_month',
        'choices': list(map(str, range(1, 13)))
    },
    'bloom_end_month': {
        'tbl_key': 'bloom_end_month',
        'choices': list(map(str, range(1, 13)))
    },
    'bloom_notes': 'bloom_notes',
    'care_notes': 'care_notes',
    'propagation_notes': 'propagation_notes',
}


class AddSpeciesForm(FlaskForm):
    """Add species form"""

    common_name = StringField(label='Common name', validators=[DataRequired()])
    genus = StringField(label='Genus')
    species = StringField(label='Species')
    family = DataListField(label='Family', default='None')
    habit = SelectField(label='Habit', default='None')
    duration = SelectField(label='Duration', choices=list_with_default(DurationType), default='')
    is_native = SelectField(label='Native?', choices=bool_with_unknown_list, default='unknown')
    water_requirement = SelectField(
        label='Water Requirement',
        choices=list_with_default(WaterRequirementType),
        default=''
    )
    light_requirement = SelectField(
        label='Light Requirement',
        choices=list_with_default(LightRequirementType),
        default=''
    )
    soil_moisture = SelectField(
        label='Soil Moisture',
        choices=list_with_default(SoilMoistureType),
        default=''
    )
    leaf_retention = SelectField(
        label='Leaf Retention',
        choices=list_with_default(LeafRetentionType),
        default=''
    )
    is_drought_tolerant = SelectField(label='Drought Tolerant?', choices=bool_with_unknown_list, default='unknown')
    is_heat_tolerant = SelectField(label='Heat Tolerant?', choices=bool_with_unknown_list, default='unknown')
    is_freeze_tolerant = SelectField(label='Freeze Tolerant?', choices=bool_with_unknown_list, default='unknown')
    usda_symbol = StringField(label='USDA Symbol')

    bloom_start_month = SelectField(label='Bloom Start', choices=list_with_default(range(1, 13)), default='')
    bloom_end_month = SelectField(label='Bloom End', choices=list_with_default(range(1, 13)), default='')
    bloom_notes = TextAreaField(label='Bloom Notes')

    care_notes = TextAreaField(label='Care Notes')
    propagation_notes = TextAreaField(label='Propagation Notes')

    submit = SubmitField('Submit')


def populate_species_form(session, form: AddSpeciesForm, species_id: int = None) -> AddSpeciesForm:
    """Handles compiling all form data for /add and /edit endpoints for species"""
    fams = [x.scientific_name for x in
            session.query(TablePlantFamily).order_by(TablePlantFamily.scientific_name).all()]
    habits = [x.plant_habit for x in
              session.query(TablePlantHabit).order_by(TablePlantHabit.plant_habit).all()]
    form.family.datalist_entries = list_with_default(fams)
    form.habit.choices = list_with_default(habits)
    if species_id is not None:
        species: TableSpecies
        species = session.query(TableSpecies).filter(TableSpecies.species_id == species_id).one_or_none()
        if species is None:
            # TODO: Probably need to throw exception on this.
            return form

        species_attr_map['family']['choices'] = fams
        species_attr_map['habit']['choices'] = habits

        form_field_map = apply_field_data_to_form(species, species_attr_map)

        # Any cleanup of data should happen here

        # Apply collected data to form
        form = populate_form(form, form_field_map)

    return form


def get_species_data_from_form(session, form_data, species_id: int = None) -> TableSpecies:
    """Handles extracting all necessary form data for /add and /edit POST endpoints for species and places it in
        a new or existing table object"""

    if species_id is not None:
        # Existing object -- replace data
        species: TableSpecies
        species = session.query(TableSpecies).filter(TableSpecies.species_id == species_id).one_or_none()
    else:
        # New family object
        species = TableSpecies()

    species = extract_form_data_to_obj(form_data=form_data, table_obj=species,
                                       obj_attr_map=species_attr_map, session=session)

    # Handle genus/species migration into scientific name field
    genus = species.genus
    species_name = species.species
    sci_name = ''
    if genus is not None:
        sci_name = f'{genus} {species_name if species_name is not None else "sp."}'
    species.scientific_name = sci_name

    return species
