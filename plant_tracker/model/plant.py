import datetime
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Enum,
    ForeignKey,
    Integer,
    VARCHAR
)
from sqlalchemy.orm import relationship

from .base import Base
from .species import TableSpecies
from .maps import TablePlantLocation


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
    plant_location_key: int = Column(ForeignKey(TablePlantLocation.plant_location_id, ondelete='SET NULL'))
    plant_location = relationship(TablePlantLocation, foreign_keys=[plant_location_key])
    is_drip_irrigated: bool = Column(Boolean)
    is_in_container: bool = Column(Boolean)
    plant_source: str = Column(Enum(PlantSourceType))
    date_planted: datetime.date = Column(Date, nullable=False)
    images = relationship('TableImage', back_populates='plant')
    observation_logs = relationship('TableObservationLog', back_populates='plant')
    maintenance_logs = relationship('TableMaintenanceLog', back_populates='plant')
    watering_logs = relationship('TableWateringLog', back_populates='plant')
    is_dead: bool = Column(Boolean, default=False)
    notes: str = Column(VARCHAR)

    def __repr__(self) -> str:
        return self.build_repr_for_class(self)
