# -*- coding: utf-8 -*-

"""SQLAlchemy models for Bio2BEL WikiPathways."""

from typing import Set

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

import pybel.dsl
from .constants import MODULE_NAME

Base = declarative_base()

PATHWAY_TABLE_NAME = f'{MODULE_NAME}_pathway'
PROTEIN_TABLE_NAME = f'{MODULE_NAME}_protein'
PROTEIN_PATHWAY_TABLE = f'{MODULE_NAME}_protein_pathway'

protein_pathway = Table(
    PROTEIN_PATHWAY_TABLE,
    Base.metadata,
    Column('protein_id', Integer, ForeignKey(f'{PROTEIN_TABLE_NAME}.id'), primary_key=True),
    Column('pathway_id', Integer, ForeignKey(f'{PATHWAY_TABLE_NAME}.id'), primary_key=True)
)


class Protein(Base):
    """A database model for a protein."""

    __tablename__ = PROTEIN_TABLE_NAME
    id = Column(Integer, primary_key=True)

    entrez_id = Column(String(255), doc='entrez id of the protein')
    hgnc_id = Column(String(255), doc='hgnc id of the protein')
    hgnc_symbol = Column(String(255), doc='hgnc symbol of the protein')

    def __repr__(self):  # noqa: D105
        return self.hgnc_id

    def serialize_to_protein_node(self) -> pybel.dsl.Protein:
        """Serialize this node to a PyBEL data dictionary."""
        return pybel.dsl.Protein(
            namespace='hgnc',
            name=self.hgnc_symbol,
            identifier=str(self.hgnc_id)
        )

    def get_pathways_ids(self) -> Set[str]:
        """Return the pathways associated with the protein."""
        return {
            pathway.wikipathways_id
            for pathway in self.pathways
        }


class Pathway(Base):
    """A database model for a WikiPathways pathway."""

    __tablename__ = PATHWAY_TABLE_NAME
    id = Column(Integer, primary_key=True)

    wikipathways_id = Column(String(255), unique=True, nullable=False, index=True, doc='WikiPathways id of the pathway')
    name = Column(String(255), doc='pathway name')

    bel_encoding = 'B'

    proteins = relationship(
        Protein,
        secondary=protein_pathway,
        backref='pathways'
    )

    def __repr__(self):  # noqa: D105
        return self.name

    def serialize_to_pathway_node(self) -> pybel.dsl.BiologicalProcess:
        """Serialize this pathway to a BEL node."""
        return pybel.dsl.BiologicalProcess(
            namespace='wikipathways',
            name=str(self.name),
            identifier=str(self.wikipathways_id),
        )

    def get_gene_set(self) -> Set[Protein]:
        """Return the genes associated with the pathway (gene set).

        Note: this function restricts to HGNC symbols genes
        """
        return {
            protein.hgnc_symbol
            for protein in self.proteins
            if protein.hgnc_symbol
        }

    @property
    def resource_id(self) -> str:
        """Return this resource's WikiPathways identifier."""
        return self.wikipathways_id

    @property
    def url(self) -> str:
        """Return a formatted URL for getting information on this resource from WikiPathways."""
        return f'https://www.wikipathways.org/index.php/Pathway:{self.wikipathways_id}'
