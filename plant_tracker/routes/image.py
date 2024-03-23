from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for
)
from pathlib import Path

from plant_tracker.forms.add_image import (
    AddImageForm,
    get_image_data_from_form,
    populate_image_form
)
from plant_tracker.forms.confirm_delete import ConfirmDeleteForm
from plant_tracker.model import TableImage
from plant_tracker.routes.helpers import (
    get_app_logger,
    get_app_eng
)

bp_image = Blueprint('image', __name__, url_prefix='/image')


@bp_image.route('/<item_type>/<int:item_id>/add', methods=['GET', 'POST'])
def add_image(item_type: str, item_id: int):
    eng = get_app_eng()
    form = AddImageForm()
    with eng.session_mgr() as session:
        form = populate_image_form(session=session, form=form)
        if request.method == 'GET':
            return render_template(
                'pages/image/add-image.jinja',
                form=form,
                is_edit=False,
                post_endpoint_url=url_for(request.endpoint, item_type=item_type, item_id=item_id)
            )
        elif request.method == 'POST':

            image_dir = Path(current_app.root_path).joinpath(f'static/images/{item_type}/{item_id}/')

            image = get_image_data_from_form(request=request, image_dir=image_dir)
            if item_type == 'species':
                image.species_key = item_id
                url = url_for('species.get_species', species_id=item_id)
            else:
                image.plant_key = item_id
                url = url_for('plant.get_plant', plant_id=item_id)
            eng.commit_and_refresh_table_obj(session=session, table_obj=image)
            flash(f'{item_type.title()} image {image.image_id} successfully added', 'success')

            return redirect(url)


@bp_image.route('/all', methods=['GET'])
@bp_image.route('/by_<item_type>/<int:item_id>/all', methods=['GET'])
def get_all_images(item_type: str = None, item_id: int = None):
    with get_app_eng().session_mgr() as session:
        if item_id:
            if item_type == 'species':
                id_filt = TableImage.species_key == item_id
            else:
                id_filt = TableImage.plant_key == item_id
            imgs = session.query(TableImage).filter(id_filt).all()
        else:
            imgs = session.query(TableImage).all()
        data_list = []
        for img in imgs:
            img: TableImage
            image_type = 'plant' if img.plant_key else 'species'
            data_list.append([
                img.image_id,
                {'image_src': img.image_path},
                image_type,
                img.species.common_name if img.species_key else f'{img.plant.species.common_name}#{img.plant_key}',
                [
                    {'url': url_for('image.delete_image', item_type=image_type, item_id=img.image_id),
                     'icon': 'bi-trash', 'val_class': 'icon delete'}
                ]
            ])
    return render_template(
        'pages/image/list-images.jinja',
        order_list=[[2, 'asc'], [3, 'asc']],
        data_rows=data_list,
        headers=['ID', 'Image', 'Type', 'Name', ''],
        table_id='images-table'
    ), 200


@bp_image.route('/<item_type>/<int:item_id>/delete', methods=['GET', 'POST'])
def delete_image(item_type: str, item_id: int):
    eng = get_app_eng()
    form = ConfirmDeleteForm()
    with eng.session_mgr() as session:
        img: TableImage

        img = session.query(TableImage).filter(TableImage.image_id == item_id).one_or_none()
        if item_type == 'species':
            url = url_for('species.get_species', species_id=item_id)
            qualifier = f'({item_type}:{img.species.common_name})'
        else:
            url = url_for('plant.get_plant', plant_id=item_id)
            qualifier = f'({item_type}:{img.plant.species.common_name}#{img.plant_key})'
        if request.method == 'GET':
            return render_template(
                'pages/confirm.jinja',
                confirm_title=f'Confirm delete of ',
                confirm_focus=f"#{img.image_id} {qualifier}",
                confirm_url=url_for('image.delete_image', item_type=item_type, item_id=item_id),
                form=form
            )
        elif request.method == 'POST':
            if request.form['confirm']:
                session.delete(img)
                flash(f'Image item #{img.image_id} successfully removed', 'success')
        return redirect(url)
