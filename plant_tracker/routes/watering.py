from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from plant_tracker.forms.add_watering import (
    AddWateringForm,
    get_watering_data_from_form,
    populate_watering_form
)
from plant_tracker.forms.confirm_delete import ConfirmDeleteForm
from plant_tracker.model import TableWateringLog
from plant_tracker.routes.helpers import (
    get_app_logger,
    get_app_eng
)

bp_watering = Blueprint('watering', __name__, url_prefix='/plant/<int:plant_id>/watering')


@bp_watering.route('/add', methods=['GET', 'POST'])
def add_watering(plant_id: int = None):
    eng = get_app_eng()
    form = AddWateringForm()
    with eng.session_mgr() as session:
        form = populate_watering_form(session=session, form=form)
        if request.method == 'GET':
            return render_template(
                'pages/watering/add-watering.html',
                form=form,
                is_edit=False,
                post_endpoint_url=url_for(request.endpoint, plant_id=plant_id)
            )
        elif request.method == 'POST':
            obs = get_watering_data_from_form(session=session, form_data=request.form)
            obs.plant_key = plant_id
            obs = eng.commit_and_refresh_table_obj(session=session, table_obj=obs)
            flash(f'watering item #{obs.watering_log_id} successfully added', 'success')
            return redirect(url_for('plant.get_plant', plant_id=plant_id))


@bp_watering.route('/<int:watering_log_id>/edit', methods=['GET', 'POST'])
def edit_watering(plant_id: int = None, watering_log_id: int = None):
    eng = get_app_eng()
    form = AddWateringForm()
    with eng.session_mgr() as session:
        form = populate_watering_form(session=session, form=form,
                                         watering_log_id=watering_log_id)
        if request.method == 'GET':
            return render_template(
                'pages/watering/add-watering.html',
                form=form,
                is_edit=True,
                post_endpoint_url=url_for(request.endpoint, plant_id=plant_id,
                                          watering_log_id=watering_log_id)
            )
        elif request.method == 'POST':
            obs = get_watering_data_from_form(
                session=session, form_data=request.form, watering_log_id=watering_log_id
            )
            session.add(obs)
            flash(f'watering item #{obs.watering_log_id} successfully updated', 'success')
            return redirect(url_for('plant.get_plant', plant_id=plant_id))


@bp_watering.route('/<int:watering_log_id>/delete', methods=['GET', 'POST'])
def delete_watering(plant_id: int = None, watering_log_id: int = None):
    eng = get_app_eng()
    form = ConfirmDeleteForm()
    with eng.session_mgr() as session:
        obs: TableWateringLog
        obs = session.query(TableWateringLog). \
            filter(TableWateringLog.watering_log_id == watering_log_id).one_or_none()
        if request.method == 'GET':
            return render_template(
                'pages/confirm.html',
                confirm_title=f'Confirm delete of ',
                confirm_focus=f"{obs.watering_type} - {obs.watering_date:%F}",
                confirm_url=url_for('watering.delete_watering',
                                    plant_id=plant_id, watering_log_id=watering_log_id),
                form=form
            )
        elif request.method == 'POST':
            if request.form['confirm']:
                session.delete(obs)
                flash(f'watering item #{obs.watering_log_id} successfully removed', 'success')
        return redirect(url_for('plant.get_plant', plant_id=plant_id))
