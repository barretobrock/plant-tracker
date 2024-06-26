from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for
)

from plant_tracker.core.utils import default_if_prop_none
from plant_tracker.core.geodata import get_all_geodata
from plant_tracker.forms.add_species import (
    AddSpeciesForm,
    get_species_data_from_form,
    populate_species_form
)
from plant_tracker.forms.confirm_delete import ConfirmDeleteForm
from plant_tracker.model import (
    LeafRetentionType,
    LightRequirementType,
    SoilMoistureType,
    TableSpecies,
    WaterRequirementType
)
from plant_tracker.routes.helpers import (
    get_app_logger,
    get_app_eng,
)

bp_species = Blueprint('species', __name__, url_prefix='/species')


@bp_species.route('/add', methods=['GET', 'POST'])
def add_species(species_id: int = None):
    eng = get_app_eng()
    form = AddSpeciesForm()
    with eng.session_mgr() as session:
        form = populate_species_form(session=session, form=form)
        if request.method == 'GET':
            return render_template(
                'pages/species/add-species.jinja',
                form=form,
                is_edit=False,
                post_endpoint_url=url_for(request.endpoint)
            )
        elif request.method == 'POST':
            species = get_species_data_from_form(session=session, form_data=request.form)
            session.add(species)
            session.commit()
            session.refresh(species)
            flash(f'Species {species.scientific_name} successfully added', 'success')
            return redirect(url_for('species.get_species', species_id=species.species_id))


@bp_species.route('/<int:species_id>/edit', methods=['GET', 'POST'])
def edit_species(species_id: int = None):
    eng = get_app_eng()
    form = AddSpeciesForm()
    with eng.session_mgr() as session:
        form = populate_species_form(session=session, form=form, species_id=species_id)
        if request.method == 'GET':
            return render_template(
                'pages/species/add-species.jinja',
                form=form,
                is_edit=True,
                post_endpoint_url=url_for(request.endpoint, species_id=species_id)
            )
        elif request.method == 'POST':
            species = get_species_data_from_form(session=session, form_data=request.form, species_id=species_id)
            session.add(species)
            flash(f'Species {species.scientific_name} successfully updated', 'success')
            return redirect(url_for('species.get_species', species_id=species_id))


@bp_species.route('/<int:species_id>', methods=['GET'])
def get_species(species_id: int):
    with (get_app_eng().session_mgr() as session):
        species: TableSpecies
        species = session.query(TableSpecies).filter(TableSpecies.species_id == species_id).one_or_none()
        fam_text = 'Unknown' if species.plant_family is None else (f'{species.plant_family.scientific_name} '
                                                                   f'({species.plant_family.common_name})')
        # Here, assign icon classes for data we want to attribute as an icon
        icon_class_map = {
            'Water Requirement': {
                'addl_class': 'waterreq',
                'value': default_if_prop_none(species, 'water_requirement', ''),
                'map': {
                    '': 'bi-question',
                    WaterRequirementType.LOW: 'bi-droplet',
                    WaterRequirementType.MED: 'bi-droplet-half',
                    WaterRequirementType.HIGH: 'bi-droplet-fill'
                }
            },
            'Light Requirement': {
                'addl_class': 'lightreq',
                'value': default_if_prop_none(species, 'light_requirement', ''),
                'map': {
                    '': 'bi-question',
                    LightRequirementType.FULLSUN: 'bi-sun-fill',
                    LightRequirementType.PARTSUN: 'bi-brightness-alt-high-fill',
                    LightRequirementType.PARTSHADE: 'bi-cloud-sun',
                    LightRequirementType.FULLSHADE: 'bi-cloud',
                }
            },
            'Leaf Retention': {
                'addl_class': 'leafret',
                'value': default_if_prop_none(species, 'leaf_retention', ''),
                'map': {
                    '': 'bi-question',
                    LeafRetentionType.DECIDUOUS: 'bi-tree',
                    LeafRetentionType.SEMIEVERGREEN: 'bi-star-half',
                    LeafRetentionType.EVERGREEN: 'bi-tree-fill',
                }
            },
            'Soil Moisture': {
                'addl_class': 'soilmoist',
                'value': default_if_prop_none(species, 'soil_moisture', ''),
                'map': {
                    '': 'bi-question',
                    SoilMoistureType.DRY: 'bi-align-bottom',
                    SoilMoistureType.MOIST: 'bi-align-center',
                    SoilMoistureType.WET: 'bi-align-top',
                }
            }
        }

        basic_info = {
            'Family': {'value': fam_text},
            'Habit': {'value': default_if_prop_none(species, 'habit.plant_habit', '?')},
            'Duration': {'value': default_if_prop_none(species, 'duration', '?')},
            'Drought Tolerant':  {'value': default_if_prop_none(species, 'is_drought_tolerant', '?')},
            'Heat Tolerant': {'value': default_if_prop_none(species, 'is_heat_tolerant', '?')},
            'Freeze Tolerant': {'value': default_if_prop_none(species, 'is_freeze_tolerant', '?')}
        }
        scheduled_maint_info = {
            'headers': ["Type", "Freq", "Start", "End", "Notes", ""],
            'rowdata': [
                [
                    x.maintenance_type,
                    x.maintenance_frequency,
                    x.maintenance_period_start.strftime("%b %d"),
                    x.maintenance_period_end.strftime("%b %d"),
                    x.notes,
                    [
                        {'url': url_for('scheduled_maintenance.edit_scheduled_maintenance', species_id=species_id,
                                        maintenance_schedule_id=x.maintenance_schedule_id),
                         'icon': 'bi-pencil', 'val_class': 'icon edit me-1'},
                        {'url': url_for('scheduled_maintenance.delete_scheduled_maintenance',
                                        species_id=species_id,
                                        maintenance_schedule_id=x.maintenance_schedule_id),
                         'icon': 'bi-trash', 'val_class': 'icon delete me-1'},
                    ]
                ] for x in species.scheduled_maintenance_logs]
        }

        focus_ids = []
        for plant in species.plants:
            if plant.plant_location:
                focus_ids.append(plant.plant_location.geodata_key)
        map_points = get_all_geodata(session=session, focus_ids=focus_ids)

        return render_template(
            'pages/species/species-info.jinja',
            data=species,
            icon_class_map=icon_class_map,
            basic_info=basic_info,
            scheduled_maint_info=scheduled_maint_info,
            map_points=map_points
        )


@bp_species.route('/all', methods=['GET'])
def get_all_species():
    with get_app_eng().session_mgr() as session:
        species = session.query(TableSpecies).all()
        data_list = []
        sp: TableSpecies
        for sp in species:
            sp_id = sp.species_id
            fam_name = default_if_prop_none(sp, 'plant_family.scientific_name', '')
            wf_link = f'https://www.wildflower.org/plants/result.php?id_plant={sp.usda_symbol}' if sp.usda_symbol else ''
            if sp.is_native is None:
                native_icon = 'question'
            elif sp.is_native:
                native_icon = 'check'
            else:
                native_icon = 'x'
            data_list.append([
                {'url': url_for('species.get_species', species_id=sp_id), 'text': sp_id,
                 'icon': 'bi-info-circle'},
                f'{sp.genus} {sp.species}',
                sp.common_name,
                fam_name,
                {'icon': f'bi-{native_icon}', 'val_class': 'icon bool'},
                {'url': wf_link, 'text': sp.usda_symbol},
                {'text': len(sp.plants), 'val_class': 'zero' if len(sp.plants) == 0 else ''},
                [
                    {'url': url_for('plant.add_plant', species_id=sp_id), 'icon': 'bi-plus-circle',
                     'val_class': 'icon add me-1'},
                    {'url': url_for('species.edit_species', species_id=sp_id), 'icon': 'bi-pencil',
                     'val_class': 'icon edit me-1'},
                    {'url': url_for('species.delete_species', species_id=sp_id),
                     'icon': 'bi-trash', 'val_class': 'icon delete'}
                ]
            ])
    return render_template(
        'pages/species/list-species.jinja',
        order_list=[2, 'asc'],
        data_rows=data_list,
        headers=['ID', 'Scientific', 'Common Name', 'Family', 'Native', 'WF', 'Plants', ''],
        table_id='species-table',
    ), 200


@bp_species.route('/<int:species_id>/delete', methods=['GET', 'POST'])
def delete_species(species_id: int = None):
    eng = get_app_eng()
    form = ConfirmDeleteForm()
    with eng.session_mgr() as session:
        species: TableSpecies
        species = session.query(TableSpecies). \
            filter(TableSpecies.species_id == species_id).one_or_none()
        if request.method == 'GET':
            return render_template(
                'pages/confirm.jinja',
                confirm_title=f'Confirm delete of ',
                confirm_focus=species.scientific_name,
                confirm_url=url_for('species.delete_species', species_id=species_id),
                form=form
            )
        elif request.method == 'POST':
            if request.form['confirm']:
                session.delete(species)
                flash(f'Species {species.scientific_name} successfully removed', 'success')
        return redirect(url_for('species.get_all_species'))
