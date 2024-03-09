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
from flask_cors import cross_origin

from plant_tracker.forms.add_family import (
    AddFamilyForm,
    get_family_data_from_form,
    populate_family_form
)
from plant_tracker.forms.confirm_delete import ConfirmDeleteForm
from plant_tracker.model import TablePlantFamily
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
                'pages/family/add-family.html',
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
                'pages/family/add-family.html',
                form=form,
                is_edit=True,
                post_endpoint_url=url_for(request.endpoint, family_id=family_id)
            )
        elif request.method == 'POST':
            family = get_family_data_from_form(session=session, form_data=request.form, family_id=family_id)
            session.add(family)
            flash(f'Family {family.scientific_name} successfully updated', 'success')
            return redirect(url_for('family.get_all_families'))


@bp_family.route('/api/<int:family_id>', methods=['GET'])
@bp_family.route('/<int:family_id>', methods=['GET'])
def get_family(family_id: int):
    with get_app_eng().session_mgr() as session:
        fam = session.query(TablePlantFamily).filter(TablePlantFamily.plant_family_id == family_id).one_or_none()
        if '/api/' in request.path:
            return jsonify(fam), 200
        return render_template('pages/family/family-info.html', data=fam)


@bp_family.route('/api/all', methods=['GET'])
@bp_family.route('/all', methods=['GET'])
def get_all_families():
    with get_app_eng().session_mgr() as session:
        fams = session.query(TablePlantFamily).all()
        if '/api/' in request.path:
            return jsonify(fams), 200
        data_list = []
        fm: TablePlantFamily
        for fm in fams:
            fm_id = fm.plant_family_id
            data_list.append({
                'id': {'url': url_for('family.get_family', family_id=fm_id), 'name': fm_id},
                'scientific_name': fm.scientific_name,
                'common_name': fm.common_name,
                '': [
                    {'url': url_for('family.edit_family', family_id=fm_id),
                     'icon': 'bi-pencil', 'icon_class': 'icon edit me-1'},
                    {'url': url_for('family.delete_family', family_id=fm_id),
                     'icon': 'bi-trash', 'icon_class': 'icon delete'}
                ]
            })
    return render_template(
        'pages/family/list-families.html',
        order_list=[1, 'asc'],
        data_rows=data_list,
        headers=['ID', 'Scientific Name', 'Common Name', ''],
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
                'pages/confirm.html',
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
