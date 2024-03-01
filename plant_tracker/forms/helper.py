from enum import StrEnum, EnumType
from typing import (
    Dict,
    Iterable,
    List,
    Type,
    Union
)

from wtforms import (
    FormField,
    Form,
    StringField
)

bool_with_unknown_list = ['unknown', 'yes', 'no']


class DataListField(StringField):
    # This should be overridden on population
    datalist_entries = []


def list_with_default(obj: Union[List[str], Type[StrEnum], Iterable], default: str = '') -> List[str]:
    if isinstance(obj, (EnumType, range)):
        obj = list(obj)
    return [default] + obj


def populate_form(form: Form, field_map: Dict[str, Union[str, bool]]) -> Form:
    """Handles populating edit forms with data"""
    for field, item in field_map.items():
        if isinstance(item, bool):
            if item is None:
                form[field].data = 'None'
            else:
                form[field].data = item
        elif isinstance(item, dict):
            form[field].choices = item['choices']
            form[field].default = item['default']
            form[field].data = item['default']
        else:
            form[field].data = item
    return form
