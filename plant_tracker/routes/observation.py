from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from plant_tracker.forms.add_observation import (
    AddObservationForm,
    get_observation_data_from_form,
    populate_observation_form
)
from plant_tracker.forms.confirm_delete import ConfirmDeleteForm
from plant_tracker.model import TableObservationLog
from plant_tracker.routes.helpers import (
    get_app_logger,
    get_app_eng
)

bp_obs = Blueprint('observation', __name__, url_prefix='/plant/<int:plant_id>/observation')


@bp_obs.route('/add', methods=['GET', 'POST'])
def add_observation(plant_id: int = None):
    eng = get_app_eng()
    form = AddObservationForm()
    with eng.session_mgr() as session:
        form = populate_observation_form(session=session, form=form)
        if request.method == 'GET':
            return render_template(
                'pages/observation/add-observation.html',
                form=form,
                is_edit=False,
                post_endpoint_url=url_for(request.endpoint, plant_id=plant_id)
            )
        elif request.method == 'POST':
            obs = get_observation_data_from_form(session=session, form_data=request.form)
            obs.plant_key = plant_id
            obs = eng.commit_and_refresh_table_obj(session=session, table_obj=obs)
            flash(f'Observation item #{obs.observation_log_id} successfully added', 'success')
            return redirect(url_for('plant.get_plant', plant_id=plant_id))


@bp_obs.route('/<int:observation_log_id>/edit', methods=['GET', 'POST'])
def edit_observation(plant_id: int = None, observation_log_id: int = None):
    eng = get_app_eng()
    form = AddObservationForm()
    with eng.session_mgr() as session:
        form = populate_observation_form(session=session, form=form,
                                         observation_log_id=observation_log_id)
        if request.method == 'GET':
            return render_template(
                'pages/observation/add-observation.html',
                form=form,
                is_edit=True,
                post_endpoint_url=url_for(request.endpoint, plant_id=plant_id,
                                          observation_log_id=observation_log_id)
            )
        elif request.method == 'POST':
            obs = get_observation_data_from_form(
                session=session, form_data=request.form, observation_log_id=observation_log_id
            )
            session.add(obs)
            flash(f'Observation item #{obs.observation_log_id} successfully updated', 'success')
            return redirect(url_for('plant.get_plant', plant_id=plant_id))


@bp_obs.route('/<int:observation_log_id>/delete', methods=['GET', 'POST'])
def delete_observation(plant_id: int = None, observation_log_id: int = None):
    eng = get_app_eng()
    form = ConfirmDeleteForm()
    with eng.session_mgr() as session:
        obs: TableObservationLog
        obs = session.query(TableObservationLog). \
            filter(TableObservationLog.observation_log_id == observation_log_id).one_or_none()
        if request.method == 'GET':
            return render_template(
                'pages/confirm.html',
                confirm_title=f'Confirm delete of ',
                confirm_focus=f"{obs.observation_type} - {obs.observation_date:%F}",
                confirm_url=url_for('observation.delete_observation',
                                    plant_id=plant_id, observation_log_id=observation_log_id),
                form=form
            )
        elif request.method == 'POST':
            if request.form['confirm']:
                session.delete(obs)
                flash(f'Observation item #{obs.observation_log_id} successfully removed', 'success')
        return redirect(url_for('plant.get_plant', plant_id=plant_id))
