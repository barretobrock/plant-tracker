from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for
)

from plant_tracker.forms.add_family import (
    AddFamilyForm,
    get_family_data_from_form,
    populate_family_form
)
from plant_tracker.forms.confirm_delete import ConfirmDeleteForm
from plant_tracker.model import (
    TablePlantFamily,
    TableSpecies
)
from plant_tracker.routes.helpers import (
    get_app_logger,
    get_app_eng
)

bp_family = Blueprint('family', __name__, url_prefix='/family')


@bp_family.route('/add', methods=['GET', 'POST'])
def add_family():
    eng = get_app_eng()
    form = AddFamilyForm()
    with eng.session_mgr() as session:
        form = populate_family_form(session=session, form=form)
        if request.method == 'GET':
            return render_template(
                'pages/family/add-family.jinja',
                form=form,
                is_edit=False,
                post_endpoint_url=url_for(request.endpoint)
            )
        elif request.method == 'POST':
            family = get_family_data_from_form(session=session, form_data=request.form)
            session.add(family)
            session.commit()
            session.refresh(family)
            flash(f'Family {family.scientific_name} successfully added', 'success')
            return redirect(url_for('family.get_family', family_id=family.plant_family_id))


@bp_family.route('/<int:family_id>/edit', methods=['GET', 'POST'])
def edit_family(family_id: int):
    eng = get_app_eng()
    form = AddFamilyForm()
    with eng.session_mgr() as session:
        form = populate_family_form(session=session, form=form, family_id=family_id)
        if request.method == 'GET':
            return render_template(
                'pages/family/add-family.jinja',
                form=form,
                is_edit=True,
                post_endpoint_url=url_for(request.endpoint, family_id=family_id)
            )
        elif request.method == 'POST':
            family = get_family_data_from_form(session=session, form_data=request.form, family_id=family_id)
            session.add(family)
            flash(f'Family {family.scientific_name} successfully updated', 'success')
            return redirect(url_for('family.get_all_families'))


@bp_family.route('/<int:family_id>', methods=['GET'])
def get_family(family_id: int):
    with get_app_eng().session_mgr() as session:
        fam = session.query(TablePlantFamily).filter(TablePlantFamily.plant_family_id == family_id).one_or_none()
        return render_template('pages/family/family-info.jinja', data=fam)


@bp_family.route('/all', methods=['GET'])
def get_all_families():
    with get_app_eng().session_mgr() as session:
        fams = session.query(TablePlantFamily).all()
        spp = session.query(TableSpecies).all()
        # Group species by family id
        fam_map = {}
        for sp in spp:
            if sp.plant_family_key is None:
                continue
            if sp.plant_family_key in fam_map.keys():
                fam_map[sp.plant_family_key] += 1
            else:
                fam_map[sp.plant_family_key] = 1
        data_list = []
        fm: TablePlantFamily
        for fm in fams:
            fm_id = fm.plant_family_id
            data_list.append([
                {'url': url_for('family.get_family', family_id=fm_id), 'text': fm_id,
                 'icon': 'bi-info-circle'},
                fm.scientific_name,
                fm.common_name,
                fam_map.get(fm_id, 0),
                [
                    {'url': url_for('family.edit_family', family_id=fm_id),
                     'icon': 'bi-pencil', 'val_class': 'icon edit me-1'},
                    {'url': url_for('family.delete_family', family_id=fm_id),
                     'icon': 'bi-trash', 'val_class': 'icon delete'}
                ]
            ])
    return render_template(
        'pages/family/list-families.jinja',
        order_list=[3, 'desc'],
        data_rows=data_list,
        headers=['ID', 'Scientific Name', 'Common Name', 'Sp Count', ''],
        table_id='families-table'
    ), 200


@bp_family.route('/<int:family_id>/delete', methods=['GET', 'POST'])
def delete_family(family_id: int):
    eng = get_app_eng()
    form = ConfirmDeleteForm()
    with eng.session_mgr() as session:
        family: TablePlantFamily
        family = session.query(TablePlantFamily). \
            filter(TablePlantFamily.plant_family_id == family_id).one_or_none()
        if request.method == 'GET':
            return render_template(
                'pages/confirm.jinja',
                confirm_title=f'Confirm delete of ',
                confirm_focus=family.scientific_name,
                confirm_url=url_for('family.delete_family', family_id=family_id),
                form=form
            )
        elif request.method == 'POST':
            if request.form['confirm']:
                session.delete(family)
                flash(f'Family {family.scientific_name} successfully removed', 'success')
        return redirect(url_for('family.get_all_families'))
