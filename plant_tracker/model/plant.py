import datetime
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import (
    VARCHAR,
    Boolean,
    Column,
    Date,
    Enum,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import relationship

from .base import Base
from .species import TableSpecies
from .maps import TablePlantRegion, TablePlantSubRegion, TablePolypoint


class PlantSourceType(StrEnum):
    RESCUE = 'rescue'
    NURSERY = 'nursery'
    FOUND_IN_YARD = 'found_in_yard'
    NPSOT = 'npsot'
    ORDERED_ONLINE = 'ordered_online'
    OTHER = 'other'


@dataclass
class TablePlant(Base):
    """plant table"""

    plant_id: int = Column(Integer, primary_key=True, autoincrement=True)
    species_key: int = Column(ForeignKey(TableSpecies.species_id, ondelete='CASCADE'), nullable=False)
    species = relationship('TableSpecies', back_populates='plants')
    region_key: int = Column(ForeignKey(TablePlantRegion.region_id, ondelete='SET NULL'))
    region = relationship(TablePlantRegion, foreign_keys=[region_key])
    sub_region_key: int = Column(ForeignKey(TablePlantSubRegion.sub_region_id, ondelete='SET NULL'))
    sub_region = relationship(TablePlantSubRegion, foreign_keys=[sub_region_key])
    polypoint_key: int = Column(ForeignKey(TablePolypoint.polypoint_id, ondelete='SET NULL'))
    is_drip_irrigated: bool = Column(Boolean)
    is_in_container: bool = Column(Boolean)
    plant_source = Column(Enum(PlantSourceType))
    date_planted: datetime.date = Column(Date, nullable=False)
    images = relationship('TablePlantImage', back_populates='plant')
    observation_logs = relationship('TableObservationLog', back_populates='plant')
    maintenance_logs = relationship('TableMaintenanceLog', back_populates='plant')
    watering_logs = relationship('TableWateringLog', back_populates='plant')
    is_dead: bool = Column(Boolean, default=False)

    def __repr__(self) -> str:
        return self.build_repr_for_class(self)


@dataclass
class TablePlantImage(Base):
    """plant_image"""
    plant_image_id: int = Column(Integer, primary_key=True, autoincrement=True)
    plant_key: int = Column(ForeignKey(TablePlant.plant_id, ondelete='CASCADE'), nullable=False)
    plant = relationship('TablePlant', back_populates='images')
    image_url: str = Column(VARCHAR, nullable=False, unique=True)

    def __repr__(self) -> str:
        return self.build_repr_for_class(self)
