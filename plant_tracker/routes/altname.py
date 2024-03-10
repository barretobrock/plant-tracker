from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from plant_tracker.forms.add_name import (
    AddNameForm,
    get_name_data_from_form,
    populate_name_form
)
from plant_tracker.forms.confirm_delete import ConfirmDeleteForm
from plant_tracker.model import TableAlternateNames
from plant_tracker.routes.helpers import (
    get_app_logger,
    get_app_eng
)

bp_altname = Blueprint('altname', __name__, url_prefix='/species/<int:species_id>/altname')


@bp_altname.route('/add', methods=['GET', 'POST'])
def add_altname(species_id: int):
    eng = get_app_eng()
    form = AddNameForm()
    with eng.session_mgr() as session:
        form = populate_name_form(session=session, form=form)
        if request.method == 'GET':
            return render_template(
                'pages/altname/add-altname.html',
                form=form,
                is_edit=False,
                post_endpoint_url=url_for(request.endpoint, species_id=species_id)
            )
        elif request.method == 'POST':
            altname = get_name_data_from_form(session=session, form_data=request.form)
            altname.species_key = species_id
            session.add(altname)
            session.commit()
            session.refresh(altname)
            flash(f'Species alternative name {altname.alternate_name_id} successfully added', 'success')
            return redirect(url_for('species.get_species', species_id=species_id))


@bp_altname.route('/<int:alternate_name_id>/edit', methods=['GET', 'POST'])
def edit_altname(species_id: int = None, alternate_name_id: int = None):
    eng = get_app_eng()
    form = AddNameForm()
    with eng.session_mgr() as session:
        form = populate_name_form(session=session, form=form, alternate_name_id=alternate_name_id)
        if request.method == 'GET':
            return render_template(
                'pages/altname/add-altname.html',
                form=form,
                is_edit=True,
                post_endpoint_url=url_for(request.endpoint, species_id=species_id, alternate_name_id=alternate_name_id)
            )
        elif request.method == 'POST':
            altname = get_name_data_from_form(session=session, form_data=request.form,
                                              alternate_name_id=alternate_name_id)
            session.add(altname)
            flash(f'Alternate name #{altname.alternate_name_id} successfully updated', 'success')
            return redirect(url_for('species.get_species', species_id=species_id))


@bp_altname.route('/<int:alternate_name_id>/delete', methods=['GET', 'POST'])
def delete_alt_name(species_id: int = None, alternate_name_id: int = None):
    eng = get_app_eng()
    form = ConfirmDeleteForm()
    with eng.session_mgr() as session:
        altname: TableAlternateNames
        altname = session.query(TableAlternateNames). \
            filter(TableAlternateNames.alternate_name_id == alternate_name_id).one_or_none()
        if request.method == 'GET':
            return render_template(
                'pages/confirm.html',
                confirm_title=f'Confirm delete of ',
                confirm_focus=altname.name,
                confirm_url=url_for('altname.delete_alt_name', species_id=species_id,
                                    alternate_name_id=alternate_name_id),
                form=form
            )
        elif request.method == 'POST':
            if request.form['confirm']:
                session.delete(altname)
                flash(f'Species alternate name "{altname.name}" successfully removed', 'success')
        return redirect(url_for('species.get_species', species_id=species_id))
