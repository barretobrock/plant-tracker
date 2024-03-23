from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from plant_tracker.forms.add_scheduled_maintenance import (
    AddScheduledMaintenanceForm,
    get_scheduled_maintenance_data_from_form,
    populate_scheduled_maintenance_form
)
from plant_tracker.forms.confirm_delete import ConfirmDeleteForm
from plant_tracker.model import TableScheduledMaintenanceLog
from plant_tracker.routes.helpers import (
    get_app_logger,
    get_app_eng
)

bp_schmaint = Blueprint('scheduled_maintenance', __name__,
                        url_prefix='/species/<int:species_id>/scheduled_maintenance')


@bp_schmaint.route('/add', methods=['GET', 'POST'])
def add_scheduled_maintenance(species_id: int = None):
    eng = get_app_eng()
    form = AddScheduledMaintenanceForm()
    with eng.session_mgr() as session:
        form = populate_scheduled_maintenance_form(session=session, form=form)
        if request.method == 'GET':
            return render_template(
                'pages/scheduled-maintenance/add-scheduled-maintenance.jinja',
                form=form,
                is_edit=False,
                post_endpoint_url=url_for(request.endpoint, species_id=species_id)
            )
        elif request.method == 'POST':
            schmaint = get_scheduled_maintenance_data_from_form(session=session, form_data=request.form)
            schmaint.species_key = species_id
            session.add(schmaint)
            session.commit()
            session.refresh(schmaint)
            flash(f'Scheduled maintenace #{schmaint.maintenance_schedule_id} successfully added', 'success')
            return redirect(url_for('species.get_species', species_id=species_id))


@bp_schmaint.route('/<int:maintenance_schedule_id>/edit', methods=['GET', 'POST'])
def edit_scheduled_maintenance(species_id: int = None, maintenance_schedule_id: int = None):
    eng = get_app_eng()
    form = AddScheduledMaintenanceForm()
    with eng.session_mgr() as session:
        form = populate_scheduled_maintenance_form(session=session, form=form,
                                                   maintenance_schedule_id=maintenance_schedule_id)
        if request.method == 'GET':
            return render_template(
                'pages/scheduled-maintenance/add-scheduled-maintenance.jinja',
                form=form,
                is_edit=True,
                post_endpoint_url=url_for(request.endpoint, species_id=species_id,
                                          maintenance_schedule_id=maintenance_schedule_id)
            )
        elif request.method == 'POST':
            schmaint = get_scheduled_maintenance_data_from_form(
                session=session, form_data=request.form, maintenance_schedule_id=maintenance_schedule_id
            )
            session.add(schmaint)
            flash(f'Scheduled maintenace #{schmaint.maintenance_schedule_id} successfully updated', 'success')
            return redirect(url_for('species.get_species', species_id=species_id))


@bp_schmaint.route('/<int:maintenance_schedule_id>/delete', methods=['GET', 'POST'])
def delete_scheduled_maintenance(species_id: int = None, maintenance_schedule_id: int = None):
    eng = get_app_eng()
    form = ConfirmDeleteForm()
    with eng.session_mgr() as session:
        schmaint: TableScheduledMaintenanceLog
        schmaint = session.query(TableScheduledMaintenanceLog). \
            filter(TableScheduledMaintenanceLog.maintenance_schedule_id == maintenance_schedule_id).one_or_none()
        if request.method == 'GET':
            return render_template(
                'pages/confirm.jinja',
                confirm_title=f'Confirm delete of ',
                confirm_focus=f"{schmaint.maintenance_type} - {schmaint.maintenance_frequency}",
                confirm_url=url_for('scheduled_maintenance.delete_scheduled_maintenance',
                                    species_id=species_id, maintenance_schedule_id=maintenance_schedule_id),
                form=form
            )
        elif request.method == 'POST':
            if request.form['confirm']:
                session.delete(schmaint)
                flash(f'Scheduled maintenance #{schmaint.maintenance_schedule_id} successfully removed', 'success')
        return redirect(url_for('species.get_species', species_id=species_id))
