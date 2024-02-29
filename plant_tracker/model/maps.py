from dataclasses import dataclass

from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape, WKBElement
from shapely.geometry import Polygon
from sqlalchemy import (
    VARCHAR,
    Column,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import relationship

from .base import Base


@dataclass
class TablePlantRegion(Base):
    """plant_region"""
    region_id: int = Column(Integer, primary_key=True, autoincrement=True)
    region_name: str = Column(VARCHAR, nullable=False)
    region_poly = Column(VARCHAR, nullable=False)
    sub_regions = relationship('TablePlantSubRegion', back_populates='region')

    # TablePlantRegion(name='something', region_data='0,25555;1,25555;...')

    def __repr__(self):
        return self.build_repr_for_class(self)


@dataclass
class TablePlantSubRegion(Base):
    """plant_sub_region"""
    sub_region_id: int = Column(Integer, primary_key=True, autoincrement=True)
    region_key: int = Column(ForeignKey(TablePlantRegion.region_id, ondelete='SET NULL'))
    region = relationship('TablePlantRegion', back_populates='sub_regions')
    sub_region_name: str = Column(VARCHAR, nullable=False)
    sub_region_poly: str = Column(VARCHAR)

    def __repr__(self):
        return self.build_repr_for_class(self)
