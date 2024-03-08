from dataclasses import dataclass
from typing import (
    List,
    Tuple,
    Union
)

from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape
from shapely import affinity
from shapely.geometry import Polygon, Point, MultiPoint
from sqlalchemy import (
    VARCHAR,
    Column,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import relationship

from .base import Base


@dataclass
class TablePolypoint(Base):
    """polypoint
    In addition to plant points and groups, this can also store boundaries and other spatial references
    """

    polypoint_id: int = Column(Integer, primary_key=True, autoincrement=True)
    polygon: str = Column(VARCHAR)
    point: str = Column(VARCHAR)
    multipoint: str = Column(VARCHAR)

    def __repr__(self):
        return self.build_repr_for_class(self)

    @classmethod
    def process_shape(cls, shape_data: Union[str, List[Union[Tuple[int], Tuple[float], str]]]):
        if isinstance(shape_data, str):
            shape_data = shape_data.split(';')
        if isinstance(shape_data[0], str):
            shape_data = [tuple(map(int, x.split(','))) for x in shape_data]
        return from_shape(Polygon(shape_data))

    @classmethod
    def scale_polygon(cls, polygon, scale_factor: float = 0.2):
        # Alternatively if scale() doesn't work, try polygon.buffer(<scale_factor>, join_style=2)
        return affinity.scale(polygon, xfact=scale_factor, yfact=scale_factor)


@dataclass
class TablePlantRegion(Base):
    """plant_region"""
    region_id: int = Column(Integer, primary_key=True, autoincrement=True)
    region_name: str = Column(VARCHAR, nullable=False)
    polypoint_key: int = Column(ForeignKey(TablePolypoint.polypoint_id, ondelete='SET NULL'))
    sub_regions = relationship('TablePlantSubRegion', back_populates='region')

    def __repr__(self):
        return self.build_repr_for_class(self)


@dataclass
class TablePlantSubRegion(Base):
    """plant_sub_region"""
    sub_region_id: int = Column(Integer, primary_key=True, autoincrement=True)
    sub_region_name: str = Column(VARCHAR, nullable=False)
    polypoint_key: int = Column(ForeignKey(TablePolypoint.polypoint_id, ondelete='SET NULL'))
    region_key: int = Column(ForeignKey(TablePlantRegion.region_id, ondelete='SET NULL'))
    region = relationship('TablePlantRegion', back_populates='sub_regions')

    def __repr__(self):
        return self.build_repr_for_class(self)





