from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    SubmitField,
)
from wtforms.validators import DataRequired


class ConfirmDeleteForm(FlaskForm):
    """Confirm delete form"""
    confirm = BooleanField(
        label='Are you sure you want to delete this?',
        validators=[DataRequired()],
    )
    submit = SubmitField('Delete')
