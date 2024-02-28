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
from .plant import TablePlant
from .species import TableSpecies


class MaintenanceType(StrEnum):
    PRUNE = 'prune'
    FERTILIZE = 'fertilize'


class ObservationType(StrEnum):
    MEASUREMENT = 'measurement'
    SPROUTED = 'sprouted'
    SEEDLING = 'seedling'
    DISEASE = 'disease'
    OTHER = 'other'


@dataclass
class TableWateringLog(Base):
    """watering_log"""

    watering_log_id: int = Column(Integer, primary_key=True, autoincrement=True)
    plant_key: int = Column(ForeignKey(TablePlant.plant_id), nullable=False)
    plant = relationship('TablePlant', back_populates='watering_logs')
    watering_date: datetime.date = Column(Date, nullable=False, default=datetime.date.today())
    notes: str = Column(VARCHAR)

    def __init__(self, plant: TablePlant, watering_date: datetime.date = None, notes: str = None):
        self.plant = plant
        self.notes = notes
        if watering_date is not None:
            self.watering_date = watering_date

    def __repr__(self):
        return self.build_repr_for_class(self)


@dataclass
class TableMaintenanceLog(Base):
    """maintenance_log"""

    maintenance_log_id: int = Column(Integer, primary_key=True, autoincrement=True)
    plant_key: int = Column(ForeignKey(TablePlant.plant_id), nullable=False)
    plant = relationship('TablePlant', back_populates='maintenance_logs')
    maintenance_type = Column(Enum(MaintenanceType), nullable=False)
    maintenance_date: datetime.date = Column(Date, nullable=False, default=datetime.date.today())
    notes: str = Column(VARCHAR)

    def __init__(self, plant: TablePlant, maintenance_type: MaintenanceType,
                 maintenance_date: datetime.date = None, notes: str = None):
        self.plant = plant
        self.maintenance_type = maintenance_type
        self.notes = notes
        if maintenance_date is not None:
            self.maintenance_date = maintenance_date

    def __repr__(self):
        return self.build_repr_for_class(self)


@dataclass
class TableObservationLog(Base):
    """observation_log"""
    observation_log_id: int = Column(Integer, primary_key=True, autoincrement=True)
    plant_key: int = Column(ForeignKey(TablePlant.plant_id), nullable=False)
    plant = relationship('TablePlant', back_populates='observation_logs')
    plant_rating: int = Column(Integer)
    plant_height_mm: int = Column(Integer)
    plant_width_mm: int = Column(Integer)
    observation_type = Column(Enum(ObservationType), nullable=False)
    observation_date: datetime.date = Column(Date, nullable=False, default=datetime.date.today())
    notes: str = Column(VARCHAR)

    def __init__(
            self,
            plant: TablePlant,
            observation_type: ObservationType,
            plant_rating: int = None,
            plant_height_mm: int = None,
            plant_width_mm: int = None,
            observation_date: datetime.date = None,
            notes: str = None
    ):
        self.plant = plant
        self.plant_rating = plant_rating
        self.plant_height_mm = plant_height_mm
        self.plant_width_mm = plant_width_mm
        self.observation_type = observation_type
        self.notes = notes
        if observation_date is not None:
            self.observation_date = observation_date

    def __repr__(self):
        return self.build_repr_for_class(self)


@dataclass
class TableScheduledMaintenanceLog(Base):
    """scheduled_maintenance_log

    perhaps we schedule maintenance on the species level?
    """

    maintenance_schedule_id: int = Column(Integer, primary_key=True, autoincrement=True)
    species_key: int = Column(ForeignKey(TableSpecies.species_id), nullable=False)
    species = relationship(TableSpecies, back_populates='scheduled_maintenance_logs')
    maintenance_type = Column(Enum(MaintenanceType), nullable=False)
    maintenance_period_start_mm: int = Column(Integer, nullable=False)
    maintenance_period_start_dd: int = Column(Integer, nullable=False)
    maintenance_period_end_mm: int = Column(Integer, nullable=False)
    maintenance_period_end_dd: int = Column(Integer, nullable=False)
    notes: str = Column(VARCHAR)

    # def __init__(
    #         self,
    #         maintenance_type: MaintenanceType,
    #         maintenance_period_start_mm: int,
    #         maintenance_period_start_dd: int,
    #         maintenance_period_end_mm: int,
    #         maintenance_period_end_dd: int,
    #         species: TableSpecies = None,
    #         notes: str = None
    # ):
    #     if species is not None:
    #         self.species = species
    #     self.maintenance_type = maintenance_type,
    #     self.maintenance_period_start_mm = maintenance_period_start_mm
    #     self.maintenance_period_start_dd = maintenance_period_start_dd
    #     self.maintenance_period_end_mm = maintenance_period_end_mm
    #     self.maintenance_period_end_dd = maintenance_period_end_dd
    #     self.notes = notes

    def __repr__(self):
        return self.build_repr_for_class(self)


@dataclass
class TableScheduledWateringLog(Base):
    """scheduled_watering_log"""

    watering_schedule_id: int = Column(Integer, primary_key=True, autoincrement=True)
    species_key: int = Column(ForeignKey(TableSpecies.species_id), nullable=False)
    species = relationship(TableSpecies, back_populates='scheduled_watering_logs')
    is_enabled: bool = Column(Boolean, default=False)
    monthly_frequency_in_days: str = Column(VARCHAR)
    next_day_due: datetime.date = Column(Date)
    notes: str = Column(VARCHAR)

    def __init__(
            self,
            species: TableSpecies = None,
            is_enabled: bool = False,
            monthly_frequency_in_days: str = None,
            next_day_due: datetime.date = None,
            notes: str = None
    ):
        if species is not None:
            self.species = species
        self.is_enabled = is_enabled
        self.monthly_frequency_in_days = monthly_frequency_in_days
        self.next_day_due = next_day_due
        self.notes = notes

    def __repr__(self):
        return self.build_repr_for_class(self)
