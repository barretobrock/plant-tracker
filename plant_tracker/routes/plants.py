from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from sqlalchemy.sql import (
    and_,
    not_
)

from plant_tracker.core.utils import default_if_prop_none
from plant_tracker.core.geodata import (
    process_gdata_and_assign_location,
    get_all_geodata
)
from plant_tracker.forms.add_plant import (
    AddPlantForm,
    get_plant_data_from_form,
    populate_plant_form
)
from plant_tracker.forms.confirm_delete import ConfirmDeleteForm
from plant_tracker.model import (
    GeodataType,
    TablePlant,
    TablePlantLocation,
    TableSpecies
)
from plant_tracker.routes.helpers import (
    get_app_logger,
    get_app_eng
)

bp_plant = Blueprint('plant', __name__, url_prefix='/plant')


@bp_plant.route('/add', methods=['GET', 'POST'])
@bp_plant.route('/by_species/<int:species_id>/add', methods=['GET', 'POST'])
def add_plant(species_id: int = None):
    eng = get_app_eng()
    form = AddPlantForm()
    log = get_app_logger()
    with eng.session_mgr() as session:
        form = populate_plant_form(session=session, form=form)
        if species_id:
            species = session.query(TableSpecies).filter(TableSpecies.species_id == species_id).one_or_none()
            if species:
                form.species.data = species.common_name
                form.species.render_kw = {'disabled': ''}

        if request.method == 'GET':
            return render_template(
                'pages/plant/add-plant.jinja',
                form=form,
                is_edit=False,
                map_points=get_all_geodata(session=session),
                post_endpoint_url=url_for(request.endpoint, species_id=species_id)
            )
        elif request.method == 'POST':
            if species_id:
                # This isn't populated in the form by default since it's pre-populated
                request_form = dict(request.form)
                request_form['species'] = species.common_name
                plant = get_plant_data_from_form(session=session, form_data=request_form)
            else:
                plant = get_plant_data_from_form(session=session, form_data=request.form)
            plant = eng.commit_and_refresh_table_obj(session=session, table_obj=plant)
            if request.form.get('geodata'):
                # Ensure geodata is updated
                log.debug('Ensuring plant geodata is synced with database object... ')
                gtype_val = 'group' if request.form['shape_type'] == 'polygon' else request.form['shape_type']
                gtype = GeodataType(f'plant_{gtype_val}')
                loc_name = f'{plant.species.common_name}#{plant.plant_id}'

                if plant.plant_location is None:
                    log.debug('Creating new PlantLocation object...')
                    plant.plant_location = TablePlantLocation(plant_location_name=loc_name)

                plant.plant_location = process_gdata_and_assign_location(
                    session=session,
                    table_obj=plant.plant_location,
                    form_data=request.form,
                    geo_type=gtype,
                    alt_name=loc_name
                )
                session.add(plant)

            flash(f'Plant {plant.species.scientific_name} ({plant.plant_id}) successfully added', 'success')
            return redirect(url_for('plant.get_plant', plant_id=plant.plant_id))


@bp_plant.route('/<int:plant_id>/edit', methods=['GET', 'POST'])
def edit_plant(plant_id: int = None):
    eng = get_app_eng()
    form = AddPlantForm()
    log = get_app_logger()
    with eng.session_mgr() as session:
        form = populate_plant_form(session=session, form=form, plant_id=plant_id)
        plant = session.query(TablePlant).filter(TablePlant.plant_id == plant_id).one_or_none()
        if plant.plant_location:
            focus_ids = [plant.plant_location.geodata.geodata_id]
        else:
            focus_ids = None
        if request.method == 'GET':
            return render_template(
                'pages/plant/add-plant.jinja',
                form=form,
                is_edit=True,
                map_points=get_all_geodata(session=session, focus_ids=focus_ids),
                post_endpoint_url=url_for(request.endpoint, plant_id=plant_id)
            )
        elif request.method == 'POST':
            plant = get_plant_data_from_form(session=session, form_data=request.form, plant_id=plant_id)
            if request.form.get('geodata'):
                if plant.is_dead and plant.plant_location:
                    # Handle process of removing any geodata
                    log.debug('Plant is marked dead - handling removal of location data')
                    session.delete(plant.plant_location.geodata)
                    session.delete(plant.plant_location)
                else:
                    # Ensure geodata is updated
                    log.debug('Ensuring plant geodata is synced with database object... ')
                    gtype = GeodataType(f'plant_{request.form["shape_type"]}')

                    if plant.plant_location is None:
                        log.debug('Creating new PlantLocation object...')
                        plant.plant_location = TablePlantLocation()

                    plant.plant_location = process_gdata_and_assign_location(
                        session=session,
                        table_obj=plant.plant_location,
                        form_data=request.form,
                        geo_type=gtype,
                        alt_name=f'{plant.species.common_name}#{plant_id}'
                    )

            session.add(plant)
            flash(f'Plant {plant.species.scientific_name} ({plant.plant_id}) successfully updated', 'success')
            return redirect(url_for('plant.get_all_plants'))


@bp_plant.route('/<int:plant_id>', methods=['GET'])
def get_plant(plant_id: int):
    with get_app_eng().session_mgr() as session:
        plant: TablePlant
        plant = session.query(TablePlant).filter(TablePlant.plant_id == plant_id).one_or_none()
        if plant.plant_location:
            map_points = get_all_geodata(session=session, focus_ids=[plant.plant_location.geodata_key])
        else:
            map_points = None
        return render_template(
            'pages/plant/plant-info.jinja',
            data=plant,
            observation_info={
                'headers': ['Type', 'Rating', 'Height mm', 'Width mm', 'Date', 'Notes'],
                'rowdata': [
                    [
                        x.observation_type,
                        default_if_prop_none(x, 'plant_rating'),
                        default_if_prop_none(x, 'plant_height_mm'),
                        default_if_prop_none(x, 'plant_width_mm'),
                        x.observation_date.strftime('%F'),
                        x.notes
                    ] for x in plant.observation_logs
                ]
            },
            maintenance_info={
                'headers': ['Type', 'Date', 'Notes'],
                'rowdata': [
                    [
                        x.maintenance_type,
                        x.maintenance_date.strftime('%F'),
                        x.notes
                    ] for x in plant.maintenance_logs
                ]
            },
            watering_info={
                'headers': ['Date', 'Notes'],
                'rowdata': [
                    [
                        x.watering_date.strftime('%F'),
                        x.notes
                    ] for x in plant.watering_logs
                ]
            },
            map_points=map_points
        )


@bp_plant.route('/dead', methods=['GET'])
@bp_plant.route('/by_species/<int:species_id>/all', methods=['GET'])
@bp_plant.route('/all', methods=['GET'])
def get_all_plants(species_id: int = None):
    with get_app_eng().session_mgr() as session:
        plant_filters = []
        is_dead = False
        if species_id:
            plant_filters.append(TablePlant.species_key == species_id)
        if '/dead' in request.path:
            is_dead = True
            plant_filters.append(TablePlant.is_dead)
        else:
            plant_filters.append(not_(TablePlant.is_dead))
        plants = session.query(TablePlant).filter(and_(*plant_filters)).all()
        plant_list = []
        pt: TablePlant
        for pt in plants:
            pt_id = pt.plant_id
            plant_list.append([
                {'url': url_for('plant.get_plant', plant_id=pt_id), 'text': pt_id,
                 'icon': 'bi-info-circle'},
                pt.species.scientific_name,
                pt.species.common_name,
                default_if_prop_none(pt, 'plant_source'),
                default_if_prop_none(pt, 'date_planted'),
                default_if_prop_none(pt, 'plant_location.region.region_name'),
                default_if_prop_none(pt, 'plant_location.sub_region.sub_region_name'),
                [
                    {'url': url_for('plant.edit_plant', plant_id=pt_id),
                     'icon': 'bi-pencil', 'val_class': 'icon edit me-1'},
                    {'url': url_for('plant.delete_plant', plant_id=pt_id),
                     'icon': 'bi-trash', 'val_class': 'icon delete'}
                ]
            ])
    return render_template(
        'pages/plant/list-plants.jinja',
        order_list=[1, 'asc'],
        is_dead=is_dead,
        plant_list=plant_list,
        headers=['ID', 'Scientific Name', 'Common Name', 'Source', 'Planted', 'Region', 'Sub Region', ''],
        table_id='plants-table'
    ), 200


@bp_plant.route('/<int:plant_id>/delete', methods=['GET', 'POST'])
def delete_plant(plant_id: int):
    eng = get_app_eng()
    form = ConfirmDeleteForm()
    with eng.session_mgr() as session:
        plant: TablePlant
        plant = session.query(TablePlant). \
            filter(TablePlant.plant_id == plant_id).one_or_none()
        if request.method == 'GET':
            return render_template(
                'pages/confirm.jinja',
                confirm_title=f'Confirm delete of ',
                confirm_focus=f'{plant.species.scientific_name} ({plant.plant_id})',
                confirm_url=url_for('plant.delete_plant', plant_id=plant_id),
                form=form
            )
        elif request.method == 'POST':
            if request.form['confirm']:
                session.delete(plant)
                flash(f'Plant {plant.species.scientific_name} ({plant.plant_id}) successfully removed', 'success')
        return redirect(url_for('plant.get_all_plants'))
