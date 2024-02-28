from dataclasses import dataclass

from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape, WKBElement
from shapely.geometry import Polygon
from sqlalchemy import (
    VARCHAR,
    Column,
    Integer,
)

from .base import Base


@dataclass
class TablePlantRegion(Base):
    """plant_region"""
    plant_region_id: int = Column(Integer, primary_key=True, autoincrement=True)
    region_name: str = Column(VARCHAR, nullable=False)
    region_data: str = Column(VARCHAR, nullable=False)

    def __init__(self, region_name: str, region_data):
        self.region_name = region_name
        self.region_data = region_data

        # TablePlantRegion(name='something', region_data='[[0, 2355], [55, 2355], ...]')

    def __repr__(self):
        return self.build_repr_for_class(self)


@dataclass
class TablePlantSubRegion(Base):
    """plant_sub_region"""
    plant_sub_region_id: int = Column(Integer, primary_key=True, autoincrement=True)
    sub_region_name: str = Column(VARCHAR, nullable=False)
    sub_region_data: str = Column(VARCHAR)

    def __init__(self, sub_region_name: str, sub_region_data: str):
        self.sub_region_name = sub_region_name
        self.sub_region_data = sub_region_data

    def __repr__(self):
        return self.build_repr_for_class(self)
