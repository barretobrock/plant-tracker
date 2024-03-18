from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import (
    VARCHAR,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import relationship

from .base import Base


class GeodataType(StrEnum):
    REGION = 'region'
    SUB_REGION = 'sub_region'
    PLANT_POINT = 'plant_point'
    PLANT_GROUP = 'plant_group'
    OTHER_POINT = 'other_point'
    OTHER_POLYGON = 'other_polygon'


@dataclass
class TableGeodata(Base):
    """geodata
    In addition to plant points and groups, this can also store boundaries and other spatial references
    """

    geodata_id: int = Column(Integer, primary_key=True, autoincrement=True)
    geodata_type: str = Column(Enum(GeodataType), nullable=False)
    name: str = Column(VARCHAR, nullable=False)
    is_polygon: bool = Column(Boolean, nullable=False)
    data: str = Column(VARCHAR)

    def __repr__(self):
        return self.build_repr_for_class(self)


@dataclass
class TablePlantRegion(Base):
    """plant_region"""
    region_id: int = Column(Integer, primary_key=True, autoincrement=True)
    region_name: str = Column(VARCHAR, nullable=False)
    geodata_key: int = Column(ForeignKey(TableGeodata.geodata_id, ondelete='SET NULL'))
    geodata = relationship('TableGeodata', foreign_keys=[geodata_key], backref='region')
    sub_regions = relationship('TablePlantSubRegion', back_populates='region')
    plant_locations = relationship('TablePlantLocation', back_populates='region')

    def __repr__(self):
        return self.build_repr_for_class(self)


@dataclass
class TablePlantSubRegion(Base):
    """plant_sub_region"""
    sub_region_id: int = Column(Integer, primary_key=True, autoincrement=True)
    sub_region_name: str = Column(VARCHAR, nullable=False)
    geodata_key: int = Column(ForeignKey(TableGeodata.geodata_id, ondelete='SET NULL'))
    geodata = relationship('TableGeodata', foreign_keys=[geodata_key], backref='sub_region')
    region_key: int = Column(ForeignKey(TablePlantRegion.region_id, ondelete='SET NULL'))
    region = relationship('TablePlantRegion', back_populates='sub_regions')
    plant_locations = relationship('TablePlantLocation', back_populates='sub_region')

    def __repr__(self):
        return self.build_repr_for_class(self)


@dataclass
class TablePlantLocation(Base):
    """plant_location"""
    plant_location_id: int = Column(Integer, primary_key=True, autoincrement=True)
    plant_location_name: str = Column(VARCHAR, nullable=False)
    geodata_key: int = Column(ForeignKey(TableGeodata.geodata_id, ondelete='SET NULL'))
    geodata = relationship('TableGeodata', foreign_keys=[geodata_key], backref='plant_location')
    sub_region_key: int = Column(ForeignKey(TablePlantSubRegion.sub_region_id, ondelete='SET NULL'))
    sub_region = relationship('TablePlantSubRegion', back_populates='plant_locations')
    region_key: int = Column(ForeignKey(TablePlantRegion.region_id, ondelete='SET NULL'))
    region = relationship('TablePlantRegion', back_populates='plant_locations')

    def __repr__(self):
        return self.build_repr_for_class(self)
