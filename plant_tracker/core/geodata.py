from dataclasses import dataclass
from typing import (
    Dict,
    List,
    Optional,
    Union
)

from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from sqlalchemy.sql import (
    and_,
    not_
)

from plant_tracker.model import (
    GeodataType,
    TableGeodata,
    TablePlant,
    TablePlantLocation,
    TablePlantRegion,
    TablePlantSubRegion
)


@dataclass
class GeodataPoint:
    gid: int
    name: str
    geo_type: GeodataType
    x: float
    y: float
    r: float = 250

    @classmethod
    def from_string(cls, gd_pt: str, name: str, geo_type: GeodataType, gid: int = None):
        cls.geo_type = geo_type
        cls.gid = gid
        cls.name = name
        pts = [x.strip() for x in gd_pt.split(',')]
        if len(pts) == 3:
            cls.x, cls.y, cls.r = tuple(map(float, pts))
        elif len(pts) == 2:
            cls.x, cls.y = tuple(map(float, pts[:2]))
        else:
            raise ValueError(f'Incorrect number of points: {len(pts)}. Expected 2 or 3')
        return cls

    @classmethod
    def to_string(cls) -> str:
        return f'{cls.x},{cls.y},{cls.r}'

    @classmethod
    def to_json(cls, is_focus: bool = False) -> Dict:
        return {
            'gid': cls.gid,
            'name': cls.name,
            'type': cls.geo_type.value,
            'x': cls.x,
            'y': cls.y,
            'r': cls.r,
            'class': 'focus original' if is_focus else cls.geo_type.value
        }


@dataclass
class GeodataPolygon:
    gid: Optional[int]
    name: str
    geo_type: GeodataType
    points: List[List[float]]

    @classmethod
    def from_string(cls, gd_pts: str, name: str, geo_type: GeodataType, gid: int = None):
        cls.geo_type = geo_type
        cls.name = name
        cls.gid = gid
        pts = []
        coords = gd_pts.split('\n')
        for coord in coords:
            coord = coord.strip()
            if coord == '':
                continue
            pts.append([float(x.strip()) for x in coord.split(',')])
        cls.points = pts
        return cls

    @classmethod
    def to_string(cls) -> str:
        points = cls.points.copy()  # type: List[List[float]]
        points_str = []
        for i, coord in enumerate(points):
            points_str.append(','.join(list(map(str, coord))))
        return '\n'.join(points_str)

    @classmethod
    def to_json(cls, is_focus: bool = False) -> Dict:
        return {
            'gid': cls.gid,
            'name': cls.name,
            'type': cls.geo_type.value,
            'points': cls.to_string(),
            'class': 'focus original' if is_focus else cls.geo_type.value
        }


def get_all_geodata(session, focus_ids: List[int] = None) -> Dict[GeodataType, List[Dict]]:
    """Collects all geodata points/polygons, compiles them for processing in jinja"""
    if focus_ids is None:
        focus_ids = []
    items = {k: [] for k in list(GeodataType)}
    geodatas = session.query(TableGeodata).order_by(TableGeodata.geodata_type.asc()).all()
    geoids_and_plant_ids = session.query(TableGeodata.geodata_id, TablePlant.plant_id, TablePlant.is_drip_irrigated)\
        .join(TablePlantLocation, TablePlantLocation.geodata_key == TableGeodata.geodata_id)\
        .join(TablePlant, TablePlantLocation.plant_location_id == TablePlant.plant_location_key)\
        .filter(not_(TablePlant.is_dead)).all()
    geoid_to_plant = {x[0]: {'plant_id': x[1], 'is_irrigated': x[2]} for x in geoids_and_plant_ids}
    for gd in geodatas:
        if gd.geodata_type in ([GeodataType.PLANT_POINT, GeodataType.OTHER_POINT]):
            data = GeodataPoint.from_string(gd.data, name=gd.name, geo_type=gd.geodata_type, gid=gd.geodata_id)
        else:
            data = GeodataPolygon.from_string(gd.data, name=gd.name, geo_type=gd.geodata_type, gid=gd.geodata_id)
        data_dict = data.to_json(is_focus=gd.geodata_id in focus_ids)
        if gd.geodata_type in [GeodataType.PLANT_GROUP, GeodataType.PLANT_POINT]:
            gd_dict = geoid_to_plant.get(gd.geodata_id)
            data_dict['is_irrigated'] = gd_dict['is_irrigated']
            data_dict['plant_id'] = gd_dict['plant_id']
        items[gd.geodata_type].append(data_dict)
    return items


def get_boundaries(session) -> List[Dict]:
    """Gets regions and subregions from db to plot on a map"""
    boundaries = []

    geodatas = session.query(TableGeodata).filter(not_(
        TableGeodata.geodata_type.in_([GeodataType.PLANT_GROUP, GeodataType.PLANT_POINT, GeodataType.OTHER_POINT]))).all()
    geodata: TableGeodata
    for geodata in geodatas:
        boundaries.append({
            'type': geodata.geodata_type,
            'name': geodata.name,
            'points': geodata.data
        })

    return boundaries


GEODATA_TABLE_OBJ_TYPE = Union[TableGeodata, TablePlantLocation, TablePlantSubRegion, TablePlantRegion]


def process_gdata_and_assign_location(session, table_obj: GEODATA_TABLE_OBJ_TYPE, form_data: Dict,
                                      geo_type: GeodataType, alt_name: str = None, gid: int = None) -> GEODATA_TABLE_OBJ_TYPE:

    form_geodata_key = 'geodata' if isinstance(table_obj, TablePlantLocation) else 'data'
    geodata_name = alt_name if alt_name is not None else form_data['name']
    try:
        geodata = GeodataPoint.from_string(form_data[form_geodata_key], name=geodata_name, geo_type=geo_type, gid=gid)
        is_polygon = False
    except Exception:
        geodata = GeodataPolygon.from_string(form_data[form_geodata_key], name=geodata_name, geo_type=geo_type, gid=gid)
        is_polygon = True

    if geo_type in [GeodataType.OTHER_POINT, GeodataType.OTHER_POLYGON]:
        table_obj.name = geodata_name
        table_obj.data = geodata.to_string()
        table_obj.is_polygon = is_polygon
        table_obj.geodata_type = geo_type
    elif table_obj.geodata:
        # Apply new geodata to existing geodata object
        table_obj.geodata.name = geodata_name
        table_obj.geodata.data = geodata.to_string()
        table_obj.geodata.is_polygon = is_polygon
        table_obj.geodata.geodata_type = geo_type

    else:
        # Create a new geodata object, bind to the other object
        geo_obj = TableGeodata(
            geodata_type=geo_type,
            name=geodata_name,
            is_polygon=is_polygon,
            data=geodata.to_string()
        )
        table_obj.geodata = geo_obj

    # Extract first or only point for next section
    if is_polygon:
        pt = Point(geodata.points[0])
    else:
        pt = Point(geodata.x, geodata.y)

    if isinstance(table_obj, TablePlantRegion):
        table_obj.region_name = geodata_name
        return table_obj
    elif isinstance(table_obj, TablePlantSubRegion):
        table_obj.sub_region_name = geodata_name
        regions: List[TablePlantRegion]
        regions = session.query(TablePlantRegion).all()
        for region in regions:
            region_poly = Polygon(GeodataPolygon.from_string(
                region.geodata.data, name=region.geodata.name, geo_type=region.geodata.geodata_type).points)
            if region_poly.covers(pt):
                table_obj.region_key = region.region_id
                break
    elif isinstance(table_obj, TablePlantLocation):
        table_obj.plant_location_name = geodata_name

        sub_regions: List[TablePlantSubRegion]
        sub_regions = session.query(TablePlantSubRegion).all()
        for sub_region in sub_regions:
            sub_region_poly = Polygon(GeodataPolygon.from_string(
                sub_region.geodata.data, name=sub_region.geodata.name, geo_type=sub_region.geodata.geodata_type).points)
            if sub_region_poly.covers(pt):
                table_obj.sub_region_key = sub_region.sub_region_id
                table_obj.region_key = sub_region.region_key
                break
    return table_obj
