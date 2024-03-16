from enum import Enum
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for
)
from pathlib import Path

from plant_tracker.core.utils import default_if_prop_none
from plant_tracker.core.geodata import get_boundaries
from plant_tracker.forms.add_image import (
    AddImageForm,
    get_image_data_from_form,
    populate_image_form
)
from plant_tracker.forms.add_species import (
    AddSpeciesForm,
    get_species_data_from_form,
    populate_species_form
)
from plant_tracker.forms.confirm_delete import ConfirmDeleteForm
from plant_tracker.model import (
    DurationType,
    LeafRetentionType,
    LightRequirementType,
    SoilMoistureType,
    TableAlternateNames,
    TableImage,
    TablePlantFamily,
    TablePlantHabit,
    TableSpecies,
    WaterRequirementType
)
from plant_tracker.routes.helpers import (
    get_app_logger,
    get_app_eng,
    get_obj_attr_or_default
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
                'pages/species/add-species.html',
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
                'pages/species/add-species.html',
                form=form,
                is_edit=True,
                post_endpoint_url=url_for(request.endpoint, species_id=species_id)
            )
        elif request.method == 'POST':
            species = get_species_data_from_form(session=session, form_data=request.form, species_id=species_id)
            session.add(species)
            flash(f'Species {species.scientific_name} successfully updated', 'success')
            return redirect(url_for('species.get_species', species_id=species_id))


@bp_species.route('/api/<int:species_id>', methods=['GET'])
@bp_species.route('/<int:species_id>', methods=['GET'])
def get_species(species_id: int):
    with (get_app_eng().session_mgr() as session):
        species: TableSpecies
        species = session.query(TableSpecies).filter(TableSpecies.species_id == species_id).one_or_none()
        if '/api/' in request.path:
            return jsonify(species), 200
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

        map_info = {
            'data_points': [],
            'boundaries': get_boundaries(session=session),
            'focus_color': 'green'
        }
        for plant in species.plants:
            if plant.plant_location:
                map_info['data_points'].append({
                    'type': plant.plant_location.geodata.geodata_type,
                    'data': plant.plant_location.geodata.data,
                    'name': plant.plant_location.name,
                    'color': 'green'
                })

        return render_template(
            'pages/species/species-info.html',
            data=species,
            icon_class_map=icon_class_map,
            basic_info=basic_info,
            scheduled_maint_info=scheduled_maint_info,
            map_data=map_info
        )


@bp_species.route('/api/all', methods=['GET'])
@bp_species.route('/all', methods=['GET'])
def get_all_species():
    with get_app_eng().session_mgr() as session:
        species = session.query(TableSpecies).all()
        if '/api/' in request.path:
            session.expunge_all()
            return jsonify(species), 200
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
                sp.genus,
                sp.species,
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
        'pages/species/list-species.html',
        order_list=[3, 'asc'],
        data_rows=data_list,
        headers=['ID', 'Genus', 'Species', 'Common Name', 'Family', 'Native', 'WF', 'Plants', ''],
        table_id='species-table'
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
                'pages/confirm.html',
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


@bp_species.route('/<int:species_id>/image/add', methods=['GET', 'POST'])
def add_species_image(species_id: int):
    eng = get_app_eng()
    form = AddImageForm()
    with eng.session_mgr() as session:
        form = populate_image_form(session=session, form=form)
        if request.method == 'GET':
            return render_template(
                'pages/image/add-image.html',
                form=form,
                is_edit=False,
                post_endpoint_url=url_for(request.endpoint, species_id=species_id)
            )
        elif request.method == 'POST':
            image_dir = Path(current_app.root_path).joinpath(f'static/images/species/{species_id}/')

            image = get_image_data_from_form(request=request, image_dir=image_dir)
            image.species_key = species_id
            session.add(image)
            session.commit()
            session.refresh(image)
            flash(f'Species image {image.image_id} successfully added', 'success')
            return redirect(url_for('species.get_species', species_id=species_id))
