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

from plant_tracker.core.utils import default_if_prop_none

bool_with_unknown_list = ['unknown', 'yes', 'no']


class DataListField(StringField):
    # This should be overridden on population
    datalist_entries = []


def list_with_default(obj: Union[List[str], Type[StrEnum], Iterable], default: str = '') -> List[str]:
    if isinstance(obj, (EnumType, range)):
        obj = list(obj)
    return [default] + obj


def apply_field_data_to_form(
        table_obj,
        obj_attr_map: Dict[str, Union[str, Dict[str, Union[str, Type[StrEnum], Iterable]]]]) -> Dict:
    """
        Takes a mapping of form data and the related table object and handles applying the data
            from the table object to the form to render a pre-populated data editing form
    """
    form_field_map = {}
    for attr_name, attr_details in obj_attr_map.items():
        if isinstance(attr_details, str):
            form_field_map[attr_name] = table_obj.__getattribute__(attr_name)
        elif isinstance(attr_details, dict):
            default_var = default_if_prop_none(table_obj, attr_details['tbl_key'], attr_details.get('emtpy_var', ''))

            choices = attr_details.get('choices')
            if isinstance(default_var, bool):
                # Coerce bools back into string for select rendering
                default_var = 'yes' if default_var is True else 'no'

            form_field_map[attr_name] = {
                'default': default_if_prop_none(table_obj, attr_details['tbl_key'], default=default_var),
                'choices': list_with_default(choices, default=default_var)
            }

    return form_field_map


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


def extract_form_data_to_obj(form_data, table_obj, obj_attr_map, session):
    """Extracts form data and applies it to the table object"""
    for attr_name, attr_details in obj_attr_map.items():
        attr_form_data = form_data[attr_name]
        if attr_form_data in bool_with_unknown_list:
            if attr_form_data == 'unknown':
                attr_form_data = None
            else:
                attr_form_data = attr_form_data == 'yes'
        elif attr_form_data == '':
            # Don't apply to table object
            continue

        if isinstance(attr_details, dict):
            att_table_obj_name = attr_details['tbl_key']
        else:
            att_table_obj_name = attr_details

        if '.' in att_table_obj_name:
            # Nested value
            if not (sub_obj_class := attr_details.get('sub_obj')):
                raise ValueError(f'Table obj {table_obj.__class__.__name__}\'s mapping is missing a '
                                 f'sub_obj key for key "{att_table_obj_name}".')

            sub_obj_name, sub_obj_attr_name = att_table_obj_name.split('.', maxsplit=1)
            sub_obj = table_obj.__getattribute__(sub_obj_name)
            if sub_obj is None or sub_obj.__getattribute__(sub_obj_attr_name) != attr_form_data:
                # Swap nested objects by querying for the new one
                sub_obj = session.query(sub_obj_class).\
                    filter(sub_obj_class.__getattribute__(sub_obj_attr_name) == attr_form_data).one_or_none()
                table_obj.__setattr__(sub_obj_name, sub_obj)
        else:
            table_obj.__setattr__(att_table_obj_name, attr_form_data)

    return table_obj
