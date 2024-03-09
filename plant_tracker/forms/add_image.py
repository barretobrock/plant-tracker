import pathlib

from flask_wtf import FlaskForm
import os
import random
import string
from wtforms import (
    MultipleFileField,
    StringField,
    SubmitField
)
from werkzeug.utils import secure_filename
from wtforms.validators import DataRequired

from plant_tracker.model import TableImage
from plant_tracker.forms.helper import (
    apply_field_data_to_form,
    extract_form_data_to_obj,
    populate_form
)


image_attr_map = {
    'image_path': 'image_path',
}


class AddImageForm(FlaskForm):
    """Add image form"""

    image_path = MultipleFileField(label='Image(s) to upload', validators=[DataRequired()])

    submit = SubmitField('Submit')


def populate_image_form(session, form: AddImageForm, image_id: int = None) -> AddImageForm:
    """Handles compiling all form data for /add and /edit endpoints for plant_image"""

    if image_id is not None:
        image: TableImage
        image = session.query(TableImage).filter(TableImage.image_id == image_id).one_or_none()
        if image is None:
            return form

        form_field_map = apply_field_data_to_form(image, image_attr_map)

        # Any cleanup of data should happen here...

        form = populate_form(form, form_field_map)

    return form


def get_image_data_from_form(request, image_dir: pathlib.Path,) -> TableImage:
    """Handles extracting all necessary form data for /add endpoint for image and places it in
        a new table object"""
    org_filename, file_ext = os.path.splitext(request.files['image_path'].filename)
    rando_filename = ''.join(random.choice(string.ascii_letters) for _ in range(16))

    image_dir.mkdir(parents=True, exist_ok=True)
    image_path = image_dir.joinpath(secure_filename(rando_filename + file_ext.lower()))
    with image_path.open('wb') as fw:
        fw.write(request.files['image_path'].read())

    # image_bytes = request.files['image_path'].read()
    image = TableImage(image_path=str(image_path).split('static')[1])

    return image
