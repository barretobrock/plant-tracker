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
    x: float
    y: float
    r: float = 500

    @classmethod
    def from_string(cls, gd_pt: str):
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


@dataclass
class GeodataPolygon:
    points: List[List[float]]

    @classmethod
    def from_string(cls, gd_pts: str):
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
