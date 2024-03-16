from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from plant_tracker.core.geodata import get_boundaries
from plant_tracker.forms.add_geodata import (
    AddGeodataForm,
    get_geodata_data_from_form,
    plant_shape_map,
    populate_geodata_form
)
from plant_tracker.forms.confirm_delete import ConfirmDeleteForm
from plant_tracker.model import (
    GeodataType,
    TableGeodata
)
from plant_tracker.routes.helpers import (
    get_app_logger,
    get_app_eng
)

bp_geodata = Blueprint('geodata', __name__, url_prefix='/geodata')


@bp_geodata.route('/<geo_type>/add', methods=['GET', 'POST'])
@bp_geodata.route('/<geo_type>/plant/<int:plant_id>/add', methods=['GET', 'POST'])
def add_geodata(geo_type: str, plant_id: int = None):
    eng = get_app_eng()
    form = AddGeodataForm()
    with eng.session_mgr() as session:
        form = populate_geodata_form(session=session, form=form, geo_type_str=geo_type)
        if request.method == 'GET':
            return render_template(
                'pages/geodata/add-geodata.html',
                form=form,
                is_edit=False,
                boundaries=get_boundaries(session=session),
                post_endpoint_url=url_for(request.endpoint, geo_type=geo_type)
            )
        elif request.method == 'POST':
            pp = get_geodata_data_from_form(session=session, form_data=request.form, geo_type_str=geo_type)
            pp = eng.commit_and_refresh_table_obj(session=session, table_obj=pp)
            if geo_type in [GeodataType.PLANT_GROUP.value, GeodataType.PLANT_POINT.value]:
                flash(f'Plant location "{pp.plant_location_name}" successfully added', 'success')
            elif geo_type == GeodataType.SUB_REGION.value:
                flash(f'Sub region "{pp.sub_region_name}" successfully added', 'success')
            elif geo_type == GeodataType.REGION.value:
                flash(f'Region "{pp.region_name}" successfully added', 'success')
            else:
                flash(f'Object "{pp.name}" successfully added', 'success')
            return redirect(url_for('geodata.get_all', geo_type=geo_type))


@bp_geodata.route('/<geo_type>/<int:obj_id>/edit', methods=['GET', 'POST'])
def edit_geodata(geo_type: str, obj_id: int = None):
    eng = get_app_eng()
    form = AddGeodataForm()
    with eng.session_mgr() as session:
        form = populate_geodata_form(session=session, form=form, geo_type_str=geo_type, obj_id=obj_id)
        if request.method == 'GET':
            return render_template(
                'pages/geodata/add-geodata.html',
                form=form,
                is_edit=True,
                boundaries=get_boundaries(session=session),
                post_endpoint_url=url_for(request.endpoint, geo_type=geo_type, obj_id=obj_id)
            )
        elif request.method == 'POST':
            pp = get_geodata_data_from_form(session=session, form_data=request.form,
                                            geo_type_str=geo_type, obj_id=obj_id)
            pp = eng.commit_and_refresh_table_obj(session=session, table_obj=pp)
            if geo_type in [GeodataType.PLANT_GROUP.value, GeodataType.PLANT_POINT.value]:
                flash(f'Plant location "{pp.plant_location_name}" successfully edited', 'success')
            elif geo_type == GeodataType.SUB_REGION.value:
                flash(f'Sub region "{pp.sub_region_name}" successfully edited', 'success')
            elif geo_type == GeodataType.REGION.value:
                flash(f'Region "{pp.region_name}" successfully edited', 'success')
            else:
                flash(f'Object "{pp.value}" successfully edited', 'success')
            return redirect(url_for('geodata.get_all', geo_type=geo_type))


@bp_geodata.route('/<geo_type>/<int:obj_id>/delete', methods=['GET', 'POST'])
def delete_geodata(geo_type: str, obj_id: int = None):
    eng = get_app_eng()
    form = ConfirmDeleteForm()
    with eng.session_mgr() as session:
        pp_obj = plant_shape_map[geo_type]['obj']
        if pp_obj is TableGeodata:
            pp = session.query(TableGeodata).filter(TableGeodata.geodata_id == obj_id).one_or_none()
        else:
            pp = session.query(pp_obj).filter(pp_obj.geodata_key == obj_id).one_or_none()
        if request.method == 'GET':
            return render_template(
                'pages/confirm.html',
                confirm_title=f'Confirm delete of ',
                confirm_focus=pp,
                confirm_url=url_for('geodata.delete_geodata', geo_type=geo_type, obj_id=obj_id),
                form=form
            )
        elif request.method == 'POST':
            if request.form['confirm']:
                session.delete(pp)
                if pp_obj is not TableGeodata:
                    session.delete(pp.geodata)
                flash(f'Geodata name "{pp}" successfully removed', 'success')
        return redirect(url_for('geodata.get_all'))


@bp_geodata.route('/all', methods=['GET', 'POST'])
@bp_geodata.route('/<geo_type>/all', methods=['GET', 'POST'])
def get_all(geo_type: str = None):
    eng = get_app_eng()
    with eng.session_mgr() as session:
        if geo_type:
            geos = session.query(TableGeodata).filter(TableGeodata.geodata_type == GeodataType(geo_type)).all()
        else:
            geos = session.query(TableGeodata).all()
        data_list = []
        geo: TableGeodata
        for geo in geos:
            geo_id = geo.geodata_id
            data_list.append([
                {'text': geo_id, 'icon': 'bi-info-circle'},
                geo.name,
                geo.geodata_type,
                {'icon': f'bi-{"check" if geo.is_polygon else "x"}', 'val_class': 'icon bool'},
                [
                    {'url': url_for('geodata.edit_geodata', geo_type=geo.geodata_type, obj_id=geo_id),
                     'icon': 'bi-pencil', 'val_class': 'icon edit me-1'},
                    {'url': url_for('geodata.delete_geodata', geo_type=geo.geodata_type, obj_id=geo_id),
                     'icon': 'bi-trash', 'val_class': 'icon delete'}
                ]
            ])
    return render_template(
        'pages/geodata/list-geodata.html',
        order_list=[2, 'asc'],
        data_rows=data_list,
        headers=['ID', 'Geodata Name', 'Type', 'Is Polygon', ''],
        table_id='geodata-table'
    ), 200
