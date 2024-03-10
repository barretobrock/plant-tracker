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
    MULCH = 'mulch'
    CLEAN = 'clean'


class ScheduledMaintenanceFrequencyType(StrEnum):
    ANNUAL = 'annually'
    QUARTERLY = 'quarterly'
    MONTHLY = 'monthly'


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
    plant_key: int = Column(ForeignKey(TablePlant.plant_id, ondelete='CASCADE'), nullable=False)
    plant = relationship('TablePlant', back_populates='watering_logs')
    watering_date: datetime.date = Column(Date, nullable=False, default=datetime.date.today())
    notes: str = Column(VARCHAR)

    def __repr__(self):
        return self.build_repr_for_class(self)


@dataclass
class TableMaintenanceLog(Base):
    """maintenance_log"""

    maintenance_log_id: int = Column(Integer, primary_key=True, autoincrement=True)
    plant_key: int = Column(ForeignKey(TablePlant.plant_id, ondelete='CASCADE'), nullable=False)
    plant = relationship('TablePlant', back_populates='maintenance_logs')
    maintenance_type = Column(Enum(MaintenanceType), nullable=False)
    maintenance_date: datetime.date = Column(Date, nullable=False, default=datetime.date.today())
    notes: str = Column(VARCHAR)

    def __repr__(self):
        return self.build_repr_for_class(self)


@dataclass
class TableObservationLog(Base):
    """observation_log"""
    observation_log_id: int = Column(Integer, primary_key=True, autoincrement=True)
    plant_key: int = Column(ForeignKey(TablePlant.plant_id, ondelete='CASCADE'), nullable=False)
    plant = relationship('TablePlant', back_populates='observation_logs')
    plant_rating: int = Column(Integer)
    plant_height_mm: int = Column(Integer)
    plant_width_mm: int = Column(Integer)
    observation_type = Column(Enum(ObservationType), nullable=False)
    observation_date: datetime.date = Column(Date, nullable=False, default=datetime.date.today())
    notes: str = Column(VARCHAR)

    def __repr__(self):
        return self.build_repr_for_class(self)


@dataclass
class TableScheduledMaintenanceLog(Base):
    """scheduled_maintenance_log

    perhaps we schedule maintenance on the species level?
    """

    maintenance_schedule_id: int = Column(Integer, primary_key=True, autoincrement=True)
    species_key: int = Column(ForeignKey(TableSpecies.species_id, ondelete='CASCADE'), nullable=False)
    species = relationship(TableSpecies, back_populates='scheduled_maintenance_logs')
    is_enabled: bool = Column(Boolean, default=False)
    maintenance_type = Column(Enum(MaintenanceType), nullable=False)
    maintenance_frequency = Column(Enum(ScheduledMaintenanceFrequencyType), nullable=False,
                                   default=ScheduledMaintenanceFrequencyType.ANNUAL)
    maintenance_period_start: datetime.date = Column(Date, nullable=False)
    maintenance_period_end: datetime.date = Column(Date, nullable=False)
    next_maintenance_cycle: datetime.date = Column(Date)
    notes: str = Column(VARCHAR)

    def __repr__(self):
        return self.build_repr_for_class(self)


@dataclass
class TableScheduledWateringLog(Base):
    """scheduled_watering_log"""

    watering_schedule_id: int = Column(Integer, primary_key=True, autoincrement=True)
    species_key: int = Column(ForeignKey(TableSpecies.species_id, ondelete='CASCADE'), nullable=False)
    species = relationship(TableSpecies, back_populates='scheduled_watering_logs')
    is_enabled: bool = Column(Boolean, default=False)
    monthly_frequency_in_days: str = Column(VARCHAR)  # e.g., 12,10,8,7,7,6,6,6,7,8,10,12
    next_day_due: datetime.date = Column(Date)
    notes: str = Column(VARCHAR)

    def __repr__(self):
        return self.build_repr_for_class(self)
