from dataclasses import dataclass

from sqlalchemy import (
    VARCHAR,
    Column,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import relationship

from .base import Base
from .species import TableSpecies
from .plant import TablePlant


@dataclass
class TableImage(Base):
    """image"""
    image_id: int = Column(Integer, primary_key=True, autoincrement=True)
    plant_key: int = Column(ForeignKey(TablePlant.plant_id, ondelete='CASCADE'))
    plant = relationship('TablePlant', back_populates='images')
    species_key: int = Column(ForeignKey(TableSpecies.species_id, ondelete='CASCADE'))
    species = relationship('TableSpecies', back_populates='images')
    image_path: str = Column(VARCHAR, nullable=False, unique=True)

    def __repr__(self) -> str:
        return self.build_repr_for_class(self)
