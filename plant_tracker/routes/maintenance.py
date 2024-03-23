from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from plant_tracker.forms.add_maintenance import (
    AddMaintenanceForm,
    get_maintenance_data_from_form,
    populate_maintenance_form
)
from plant_tracker.forms.confirm_delete import ConfirmDeleteForm
from plant_tracker.model import TableMaintenanceLog
from plant_tracker.routes.helpers import (
    get_app_logger,
    get_app_eng
)

bp_maint = Blueprint('maintenance', __name__,
                     url_prefix='/plant/<int:plant_id>/maintenance')


@bp_maint.route('/add', methods=['GET', 'POST'])
def add_maintenance(plant_id: int = None):
    eng = get_app_eng()
    form = AddMaintenanceForm()
    with eng.session_mgr() as session:
        form = populate_maintenance_form(session=session, form=form)
        if request.method == 'GET':
            return render_template(
                'pages/maintenance/add-maintenance.jinja',
                form=form,
                is_edit=False,
                post_endpoint_url=url_for(request.endpoint, plant_id=plant_id)
            )
        elif request.method == 'POST':
            maint = get_maintenance_data_from_form(session=session, form_data=request.form)
            maint.plant_key = plant_id
            session.add(maint)
            session.commit()
            session.refresh(maint)
            flash(f'Maintenance item #{maint.maintenance_log_id} successfully added', 'success')
            return redirect(url_for('plant.get_plant', plant_id=plant_id))


@bp_maint.route('/<int:maintenance_log_id>/edit', methods=['GET', 'POST'])
def edit_maintenance(plant_id: int = None, maintenance_log_id: int = None):
    eng = get_app_eng()
    form = AddMaintenanceForm()
    with eng.session_mgr() as session:
        form = populate_maintenance_form(session=session, form=form,
                                         maintenance_log_id=maintenance_log_id)
        if request.method == 'GET':
            return render_template(
                'pages/maintenance/add-maintenance.jinja',
                form=form,
                is_edit=True,
                post_endpoint_url=url_for(request.endpoint, plant_id=plant_id,
                                          maintenance_log_id=maintenance_log_id)
            )
        elif request.method == 'POST':
            maint = get_maintenance_data_from_form(
                session=session, form_data=request.form, maintenance_log_id=maintenance_log_id
            )
            session.add(maint)
            flash(f'Maintenance item #{maint.maintenance_log_id} successfully updated', 'success')
            return redirect(url_for('plant.get_plant', plant_id=plant_id))


@bp_maint.route('/<int:maintenance_log_id>/delete', methods=['GET', 'POST'])
def delete_maintenance(plant_id: int = None, maintenance_log_id: int = None):
    eng = get_app_eng()
    form = ConfirmDeleteForm()
    with eng.session_mgr() as session:
        maint: TableMaintenanceLog
        maint = session.query(TableMaintenanceLog). \
            filter(TableMaintenanceLog.maintenance_log_id == maintenance_log_id).one_or_none()
        if request.method == 'GET':
            return render_template(
                'pages/confirm.jinja',
                confirm_title=f'Confirm delete of ',
                confirm_focus=f"{maint.maintenance_type} - {maint.maintenance_date:%F}",
                confirm_url=url_for('maintenance.delete_maintenance',
                                    plant_id=plant_id, maintenance_log_id=maintenance_log_id),
                form=form
            )
        elif request.method == 'POST':
            if request.form['confirm']:
                session.delete(maint)
                flash(f'Maintenance item #{maint.maintenance_log_id} successfully removed', 'success')
        return redirect(url_for('plant.get_plant', plant_id=plant_id))
