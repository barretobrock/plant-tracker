from typing import (
    List,
    Union
)

from flask_wtf import FlaskForm
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from wtforms import (
    SelectField,
    StringField,
    SubmitField,
    TextAreaField
)
from wtforms.validators import DataRequired

from plant_tracker.core.geodata import (
    GeodataPoint,
    GeodataPolygon
)
from plant_tracker.model import (
    GeodataType,
    TableGeodata,
    TablePlant,
    TablePlantLocation,
    TablePlantRegion,
    TablePlantSubRegion
)
from plant_tracker.forms.helper import populate_form


plant_shape_map = {
    GeodataType.REGION: {'obj': TablePlantRegion, 'pid': TablePlantRegion.geodata_key},
    GeodataType.SUB_REGION: {'obj': TablePlantSubRegion, 'pid': TablePlantSubRegion.geodata_key},
    GeodataType.PLANT_GROUP: {'obj': TablePlant, 'pid': TablePlant.plant_id},
    GeodataType.PLANT_POINT: {'obj': TablePlant, 'pid': TablePlant.plant_id},
    GeodataType.OTHER_POINT: {'obj': TableGeodata, 'pid': TableGeodata.geodata_id},
    GeodataType.OTHER_POLYGON: {'obj': TableGeodata, 'pid': TableGeodata.geodata_id}
}


class AddGeodataForm(FlaskForm):
    """Add geodata form"""

    geodata_type = StringField(label='Geodata Type', render_kw={'disabled': ''})
    name = StringField(label='Name', validators=[DataRequired()])
    shape_type = SelectField(
        label='Shape Type',
        validators=[DataRequired()],
        choices=['polygon', 'point'],
        default='point',
        render_kw={'disabled': ''}
    )
    data = TextAreaField(label='GeoData', validators=[DataRequired()])

    submit = SubmitField('Submit')


def populate_geodata_form(session, form: AddGeodataForm, geo_type_str: str, obj_id: int = None) -> AddGeodataForm:
    """Handles compiling all form data for geodata"""
    geo_type = GeodataType(geo_type_str)
    form['geodata_type'].data = geo_type
    shape_type = 'point' if geo_type in [GeodataType.OTHER_POINT, GeodataType.PLANT_POINT] else 'polygon'
    form['shape_type'].data = shape_type
    if obj_id is not None:
        obj_details = plant_shape_map[geo_type]
        pp: Union[TableGeodata, TablePlantSubRegion, TablePlantRegion]
        pp = session.query(obj_details['obj']).filter(obj_details['pid'] == obj_id).one_or_none()

        if pp is None:
            return form

        if geo_type in [GeodataType.OTHER_POINT, GeodataType.OTHER_POLYGON]:
            geodata_obj = pp
        else:
            geodata_obj = pp.geodata

        if geodata_obj.is_polygon:
            data = GeodataPolygon.from_string(geodata_obj.data)
        else:
            data = GeodataPoint.from_string(geodata_obj.data)

        form_field_map = {
            'geodata_type': geo_type,
            'name': geodata_obj.name,
            'data': data.to_string()
        }

        # Any cleanup of data should happen here...

        form = populate_form(form, form_field_map)

    return form


def get_geodata_data_from_form(session, form_data, geo_type_str: str, obj_id: int = None) -> \
        Union[TableGeodata, TablePlantLocation, TablePlantSubRegion, TablePlantRegion]:
    """Handles extracting all necessary form data for /add and /edit POST endpoints for family and places it in
        a new or existing table object"""
    pp: Union[TableGeodata, TablePlantLocation, TablePlantSubRegion, TablePlantRegion]
    geo_type = GeodataType(geo_type_str)
    obj_details = plant_shape_map[geo_type]
    if obj_id is not None:
        pp = session.query(obj_details['obj']).filter(obj_details['pid'] == obj_id).one_or_none()
    else:
        # New object
        pp = obj_details['obj']()

    try:
        geodata = GeodataPoint.from_string(form_data['data'])
        is_polygon = False
    except Exception:
        geodata = GeodataPolygon.from_string(form_data['data'])
        is_polygon = True
    name = form_data['name']

    if geo_type in [GeodataType.OTHER_POINT, GeodataType.OTHER_POLYGON]:
        pp.name = name
        pp.data = geodata.to_string()
        pp.is_polygon = is_polygon
        pp.geodata_type = geo_type
    else:
        # Create a new geodata, bind to the other object
        geo_obj = TableGeodata(
            geodata_type=geo_type,
            name=name,
            is_polygon=is_polygon,
            data=geodata.to_string()
        )
        pp.geodata = geo_obj

        # Extract first or only point for next section
        if is_polygon:
            pt = Point(geodata.points[0])
        else:
            pt = Point(geodata.x, geodata.y)

        # Add object-specific attributes
        if geo_type == GeodataType.REGION:
            pp.region_name = name
        elif geo_type == GeodataType.SUB_REGION:
            pp.sub_region_name = name
            regions: List[TablePlantRegion]
            regions = session.query(TablePlantRegion).all()
            for region in regions:
                region_poly = Polygon(GeodataPolygon.from_string(region.geodata.data).points)
                if region_poly.covers(pt):
                    pp.region_key = region.region_id
                    break
        elif geo_type in [GeodataType.PLANT_POINT, GeodataType.PLANT_GROUP]:
            pp.plant_location_name = name
            sub_regions: List[TablePlantSubRegion]
            sub_regions = session.query(TablePlantSubRegion).all()
            for sub_region in sub_regions:
                sub_region_poly = Polygon(GeodataPolygon.from_string(sub_region.geodata.data).points)
                if sub_region_poly.covers(pt):
                    pp.sub_region_key = sub_region.sub_region_id
                    break

    return pp
