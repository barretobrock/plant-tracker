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
from .maps import TablePlantRegion, TablePlantSubRegion


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
    species_key: int = Column(ForeignKey(TableSpecies.species_id), nullable=False)
    species = relationship('TableSpecies', back_populates='plants')
    planting_loc_x: int = Column(Integer)
    planting_loc_y: int = Column(Integer)
    plant_region_key: int = Column(ForeignKey(TablePlantRegion.plant_region_id))
    plant_region = relationship(TablePlantRegion, foreign_keys=[plant_region_key])
    plant_sub_region_key: int = Column(ForeignKey(TablePlantSubRegion.plant_sub_region_id))
    plant_sub_region = relationship(TablePlantSubRegion, foreign_keys=[plant_sub_region_key])
    is_drip_irrigated: bool = Column(Boolean)
    is_in_container: bool = Column(Boolean)
    plant_source = Column(Enum(PlantSourceType))
    date_planted: datetime.date = Column(Date, nullable=False)
    images = relationship('TablePlantImage', back_populates='plant')
    observation_logs = relationship('TableObservationLog', back_populates='plant')
    maintenance_logs = relationship('TableMaintenanceLog', back_populates='plant')
    watering_logs = relationship('TableWateringLog', back_populates='plant')
    is_dead: bool = Column(Boolean, default=False)

    def __init__(
            self,
            species: TableSpecies = None,
            species_key: int = None,
            planting_loc_x: int = None,
            planting_loc_y: int = None,
            plant_region: TablePlantRegion = None,
            plant_sub_region: TablePlantSubRegion = None,
            plant_source: PlantSourceType = None,
            date_planted: datetime.date = datetime.date.today(),
            observation_logs=None,
            maintenance_logs=None,
            watering_logs=None,
    ):
        if species is not None:
            self.species = species
        elif species_key is not None:
            self.species_key = species_key
        self.planting_loc_x = planting_loc_x
        self.planting_loc_y = planting_loc_y
        self.plant_region = plant_region
        self.plant_sub_region = plant_sub_region
        self.plant_source = plant_source
        self.date_planted = date_planted
        if observation_logs is not None:
            self.observation_logs = observation_logs
        if maintenance_logs is not None:
            self.maintenance_logs = maintenance_logs
        if watering_logs is not None:
            self.watering_logs = watering_logs

    def __repr__(self) -> str:
        return self.build_repr_for_class(self)


@dataclass
class TablePlantImage(Base):
    """plant_image"""
    plant_image_id: int = Column(Integer, primary_key=True, autoincrement=True)
    plant_key: int = Column(ForeignKey(TablePlant.plant_id), nullable=False)
    plant = relationship('TablePlant', back_populates='images')
    plant_image_url: str = Column(VARCHAR, nullable=False, unique=True)

    def __init__(self, plant_image_url: str, plant: TablePlant = None, plant_key: int = None):
        self.plant_image_url = plant_image_url
        if plant is not None:
            self.plant = plant
        if plant_key is not None:
            self.plant_key = plant_key

    def __repr__(self) -> str:
        return self.build_repr_for_class(self)
