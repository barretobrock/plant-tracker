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
from plant_tracker.core.geodata import get_all_geodata
from plant_tracker.forms.add_image import (
    AddImageForm,
    get_image_data_from_form,
    populate_image_form
)
from plant_tracker.forms.add_plant import (
    AddPlantForm,
    get_plant_data_from_form,
    populate_plant_form
)
from plant_tracker.forms.confirm_delete import ConfirmDeleteForm
from plant_tracker.model import (
    GeodataType,
    TableGeodata,
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
    with eng.session_mgr() as session:
        form = populate_plant_form(session=session, form=form)
        if species_id:
            species = session.query(TableSpecies).filter(TableSpecies.species_id == species_id).one_or_none()
            if species:
                form.species.data = species.common_name
                form.species.render_kw = {'disabled': ''}

        if request.method == 'GET':
            return render_template(
                'pages/plant/add-plant.html',
                form=form,
                is_edit=False,
                post_endpoint_url=url_for(request.endpoint)
            )
        elif request.method == 'POST':
            plant = get_plant_data_from_form(session=session, form_data=request.form)
            plant = eng.commit_and_refresh_table_obj(session=session, table_obj=plant)
            flash(f'Plant {plant.species.scientific_name} ({plant.plant_id}) successfully added', 'success')
            return redirect(url_for('plant.get_plant', plant_id=plant.plant_id))


@bp_plant.route('/<int:plant_id>/edit', methods=['GET', 'POST'])
def edit_plant(plant_id: int = None):
    eng = get_app_eng()
    form = AddPlantForm()
    with eng.session_mgr() as session:
        form = populate_plant_form(session=session, form=form, plant_id=plant_id)
        plant = session.query(TablePlant).filter(TablePlant.plant_id == plant_id).one_or_none()
        if plant.plant_location:
            focus_ids = [plant.plant_location.geodata.geodata_id]
        else:
            focus_ids = None
        if request.method == 'GET':
            return render_template(
                'pages/plant/add-plant.html',
                form=form,
                is_edit=True,
                map_points=get_all_geodata(session=session, focus_ids=focus_ids),
                post_endpoint_url=url_for(request.endpoint, plant_id=plant_id)
            )
        elif request.method == 'POST':
            plant = get_plant_data_from_form(session=session, form_data=request.form, plant_id=plant_id)
            if form['geodata'].data:
                loc_name = f'{plant.species.common_name}#{plant_id}'
                is_polygon = request.form["shape_type"] == 'polygon'
                gtype = GeodataType(f'plant_{request.form["shape_type"]}')
                gdata = request.form['geodata']
                if plant.plant_location and plant.plant_location.geodata_key:
                    # Existing data
                    if gdata != plant.plant_location.geodata.data:
                        # Update shape data
                        plant.plant_location.geodata.data = gdata
                    if gtype != plant.plant_location.geodata.geodata_type:
                        # Log change in shape
                        plant.plant_location.geodata.geodata_type = gtype
                        plant.plant_location.geodata.is_polygon = is_polygon
                else:
                    # Create new plant location
                    plant.plant_location = TablePlantLocation(
                        plant_location_name=loc_name,
                    )
                    plant.plant_location.geodata = TableGeodata(
                        geodata_type=gtype,
                        name=loc_name,
                        is_polygon=is_polygon,
                        data=gdata
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
            'pages/plant/plant-info.html',
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


@bp_plant.route('/api/all', methods=['GET'])
@bp_plant.route('/all', methods=['GET'])
@bp_plant.route('/by_species/<int:species_id>/all', methods=['GET'])
def get_all_plants(species_id: int = None):
    with get_app_eng().session_mgr() as session:
        if species_id:
            plants = session.query(TablePlant).filter(TablePlant.species_key == species_id).all()
        else:
            plants = session.query(TablePlant).all()
        if '/api/' in request.path:
            return jsonify(plants), 200
        data_list = []
        pt: TablePlant
        for pt in plants:
            pt_id = pt.plant_id
            data_list.append([
                {'url': url_for('plant.get_plant', plant_id=pt_id), 'text': pt_id,
                 'icon': 'bi-info-circle'},
                pt.species.scientific_name,
                pt.species.common_name,
                default_if_prop_none(pt, 'plant_source'),
                default_if_prop_none(pt, 'region.region_name'),
                default_if_prop_none(pt, 'sub_region.sub_region_name'),
                [
                    {'url': url_for('plant.edit_plant', plant_id=pt_id),
                     'icon': 'bi-pencil', 'val_class': 'icon edit me-1'},
                    {'url': url_for('plant.delete_plant', plant_id=pt_id),
                     'icon': 'bi-trash', 'val_class': 'icon delete'}
                ]
            ])
    return render_template(
        'pages/plant/list-plants.html',
        order_list=[1, 'asc'],
        data_rows=data_list,
        headers=['ID', 'Scientific Name', 'Common Name', 'Plant Source', 'Region', 'Sub Region', ''],
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
                'pages/confirm.html',
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


@bp_plant.route('/<int:plant_id>/image/add', methods=['GET', 'POST'])
def add_plant_image(plant_id: int):
    eng = get_app_eng()
    form = AddImageForm()
    with eng.session_mgr() as session:
        form = populate_image_form(session=session, form=form)
        if request.method == 'GET':
            return render_template(
                'pages/image/add-image.html',
                form=form,
                is_edit=False,
                post_endpoint_url=url_for(request.endpoint, plant_id=plant_id)
            )
        elif request.method == 'POST':
            image_dir = Path(current_app.root_path).joinpath(f'static/images/plant/{plant_id}/')

            image = get_image_data_from_form(request=request, image_dir=image_dir)

            image.plant_key = plant_id
            session.add(image)
            session.commit()
            session.refresh(image)
            flash(f'Plant image {image.image_id} successfully added', 'success')
            return redirect(url_for('plant.get_plant', plant_id=plant_id))
