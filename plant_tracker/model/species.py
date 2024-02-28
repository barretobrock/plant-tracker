from dataclasses import dataclass
from enum import StrEnum
from typing import List

from sqlalchemy import (
    VARCHAR,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    column_property,
    relationship
)
from sqlalchemy.sql import case

from .base import Base


class LeafRetentionType(StrEnum):
    DECIDUOUS = 'deciduous'
    SEMIEVERGREEN = 'semi-evergreen'
    EVERGREEN = 'evergreen'


class WaterRequirementType(StrEnum):
    LOW = 'low'
    MED = 'med'
    HIGH = 'high'


class LightRequirementType(StrEnum):
    FULLSUN = 'full sun'
    PARTSUN = 'part sun'
    PARTSHADE = 'part shade'
    FULLSHADE = 'full shade'


class DurationType(StrEnum):
    PERENNIAL = 'perennial'
    ANNUAL = 'annual'
    BIANNUAL = 'biannual'


@dataclass
class TablePlantFamily(Base):
    """plant_family"""
    plant_family_id: int = Column(Integer, primary_key=True, autoincrement=True)
    scientific_name: str = Column(VARCHAR, nullable=False, unique=True)
    common_name: str = Column(VARCHAR)

    def __repr__(self) -> str:
        return self.build_repr_for_class(self)


@dataclass
class TablePlantHabit(Base):
    """plant_habit"""
    plant_habit_id: int = Column(Integer, primary_key=True, autoincrement=True)
    plant_habit: str = Column(VARCHAR, nullable=False, unique=True)

    def __init__(self, plant_habit: str):
        self.plant_habit = plant_habit

    def __repr__(self) -> str:
        return self.build_repr_for_class(self)


@dataclass
class TableSpecies(Base):
    """species table"""

    species_id: int = Column(Integer, primary_key=True, autoincrement=True)
    common_name: str = Column(VARCHAR, nullable=False)
    genus: str = Column(VARCHAR)
    species: str = Column(VARCHAR)
    scientific_name: str = Column(VARCHAR)
    plant_family_key: int = Column(ForeignKey(TablePlantFamily.plant_family_id))
    plant_family = relationship(TablePlantFamily, foreign_keys=[plant_family_key])
    habit_key: int = Column(ForeignKey(TablePlantHabit.plant_habit_id))
    habit = relationship(TablePlantHabit, foreign_keys=[habit_key])
    is_native: bool = Column(Boolean)
    duration = Column(Enum(DurationType))
    water_requirement: str = Column(Enum(WaterRequirementType))
    light_requirement: str = Column(Enum(LightRequirementType))
    leaf_retention: str = Column(Enum(LeafRetentionType))
    is_drought_tolerant: bool = Column(Boolean)
    is_heat_tolerant: bool = Column(Boolean)
    is_freeze_tolerant: bool = Column(Boolean)
    usda_symbol: str = Column(VARCHAR)
    bloom_start_month: int = Column(Integer)
    bloom_end_month: int = Column(Integer)
    bloom_notes: str = Column(VARCHAR)
    care_notes: str = Column(VARCHAR)
    propagation_notes: str = Column(VARCHAR)
    alternate_names = relationship('TableAlternateNames', back_populates='species')
    plants = relationship('TablePlant', back_populates='species')
    scheduled_maintenance_logs = relationship('TableScheduledMaintenanceLog', back_populates='species')
    scheduled_watering_logs = relationship('TableScheduledWateringLog', back_populates='species')

    def __repr__(self) -> str:
        return self.build_repr_for_class(self)


@dataclass
class TableAlternateNames(Base):
    """species table"""

    alternate_name_id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(VARCHAR, nullable=False)
    species_key: int = Column(ForeignKey(TableSpecies.species_id), nullable=False)
    species = relationship(TableSpecies, back_populates='alternate_names')
    is_scientific: bool = Column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return self.build_repr_for_class(self)
