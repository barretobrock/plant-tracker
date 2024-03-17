from dataclasses import dataclass
from typing import (
    Dict,
    List
)

from sqlalchemy.sql import not_

from plant_tracker.model import (
    GeodataType,
    TableGeodata,
    TablePlantRegion,
    TablePlantSubRegion
)


@dataclass
class GeodataPoint:
    name: str
    geo_type: GeodataType
    x: float
    y: float
    r: float = 250

    @classmethod
    def from_string(cls, gd_pt: str, name: str, geo_type: GeodataType):
        cls.geo_type = geo_type
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
            'name': cls.name,
            'type': cls.geo_type.value,
            'x': cls.x,
            'y': cls.y,
            'r': cls.r,
            'class': 'focus' if is_focus else cls.geo_type.value
        }


@dataclass
class GeodataPolygon:
    name: str
    geo_type: GeodataType
    points: List[List[float]]

    @classmethod
    def from_string(cls, gd_pts: str, name: str, geo_type: GeodataType):
        cls.geo_type = geo_type
        cls.name = name
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
            'name': cls.name,
            'type': cls.geo_type.value,
            'points': cls.to_string(),
            'class': 'focus' if is_focus else cls.geo_type.value
        }


def get_all_geodata(session, focus_ids: List[int] = None) -> List[Dict]:
    """Collects all geodata points/polygons, compiles them for processing in jinja"""
    if focus_ids is None:
        focus_ids = []
    items = []
    geodatas = session.query(TableGeodata).all()
    for gd in geodatas:
        if gd.geodata_type in ([GeodataType.PLANT_POINT, GeodataType.OTHER_POINT]):
            data = GeodataPoint.from_string(gd.data, name=gd.name, geo_type=gd.geodata_type)
        else:
            data = GeodataPolygon.from_string(gd.data, name=gd.name, geo_type=gd.geodata_type)
        items.append(data.to_json(is_focus=gd.geodata_id in focus_ids))
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
