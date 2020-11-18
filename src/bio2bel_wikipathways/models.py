# -*- coding: utf-8 -*-

"""SQLAlchemy models for Bio2BEL WikiPathways."""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

import pybel.dsl
from bio2bel.compath import CompathPathwayMixin, CompathProteinMixin
from bio2bel.manager.models import SpeciesMixin
from .constants import HGNC, MODULE_NAME, WIKIPATHWAYS

Base = declarative_base()

PATHWAY_TABLE_NAME = f'{MODULE_NAME}_pathway'
PROTEIN_TABLE_NAME = f'{MODULE_NAME}_protein'
SPECIES_TABLE_NAME = f'{MODULE_NAME}_species'
PROTEIN_PATHWAY_TABLE = f'{MODULE_NAME}_protein_pathway'

protein_pathway = Table(
    PROTEIN_PATHWAY_TABLE,
    Base.metadata,
    Column('protein_id', Integer, ForeignKey(f'{PROTEIN_TABLE_NAME}.id'), primary_key=True),
    Column('pathway_id', Integer, ForeignKey(f'{PATHWAY_TABLE_NAME}.id'), primary_key=True),
)


class Species(Base, SpeciesMixin):
    """A database model for species."""

    __tablename__ = SPECIES_TABLE_NAME


class Protein(Base, CompathProteinMixin):
    """A database model for a protein."""

    __tablename__ = PROTEIN_TABLE_NAME
    id = Column(Integer, primary_key=True)  # noqa:A003

    entrez_id = Column(String(255), doc='entrez id of the protein')
    hgnc_id = Column(String(255), doc='hgnc id of the protein')
    hgnc_symbol = Column(String(255), doc='hgnc symbol of the protein')

    def __repr__(self):  # noqa: D105
        return self.hgnc_id

    def to_pybel(self) -> pybel.dsl.Protein:
        """Serialize this node to a PyBEL data dictionary."""
        return pybel.dsl.Protein(
            namespace=HGNC,
            name=self.hgnc_symbol,
            identifier=self.hgnc_id,
        )


class Pathway(CompathPathwayMixin, Base):
    """A database model for a WikiPathways pathway."""

    __tablename__ = PATHWAY_TABLE_NAME
    id = Column(Integer, primary_key=True)  # noqa:A003

    prefix = WIKIPATHWAYS
    identifier = Column(String(255), unique=True, nullable=False, index=True, doc='WikiPathways id of the pathway')
    name = Column(String(255), doc='pathway name')
    revision = Column(String(255), doc='pathway revision')

    species_id = Column(Integer, ForeignKey(f'{Species.__tablename__}.id'), nullable=False, doc='The host species')
    species = relationship(Species)

    bel_encoding = 'B'

    proteins = relationship(
        Protein,
        secondary=protein_pathway,
        backref='pathways',
    )
