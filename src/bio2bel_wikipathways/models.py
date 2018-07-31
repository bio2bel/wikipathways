# -*- coding: utf-8 -*-

"""SQLAlchemy models for Bio2BEL WikiPathways."""

from pybel.dsl import bioprocess, protein as protein_dsl
from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

TABLE_PREFIX = 'wikipathways'
PATHWAY_TABLE_NAME = '{}_pathway'.format(TABLE_PREFIX)
PROTEIN_TABLE_NAME = '{}_protein'.format(TABLE_PREFIX)
PROTEIN_PATHWAY_TABLE = '{}_protein_pathway'.format(TABLE_PREFIX)

protein_pathway = Table(
    PROTEIN_PATHWAY_TABLE,
    Base.metadata,
    Column('protein_id', Integer, ForeignKey('{}.id'.format(PROTEIN_TABLE_NAME)), primary_key=True),
    Column('pathway_id', Integer, ForeignKey('{}.id'.format(PATHWAY_TABLE_NAME)), primary_key=True)
)


class Pathway(Base):
    """A database model for a WikiPathways pathway."""

    __tablename__ = PATHWAY_TABLE_NAME

    id = Column(Integer, primary_key=True)

    wikipathways_id = Column(String(255), unique=True, nullable=False, index=True, doc='WikiPathways id of the pathway')
    name = Column(String(255), doc='pathway name')

    proteins = relationship(
        'Protein',
        secondary=protein_pathway,
        backref='pathways'
    )

    def __repr__(self):  # noqa: D105
        return self.name

    def serialize_to_pathway_node(self):
        """Serialize this pathway to a BEL node.

        :rtype: pybel.dsl.bioprocess
        """
        return bioprocess(
            namespace='wikipathways',
            name=str(self.name),
            identifier=str(self.wikipathways_id)
        )

    def get_gene_set(self):
        """Return the genes associated with the pathway (gene set).

        Note: this function restricts to HGNC symbols genes

        :rtype: set[bio2bel_wikipathways.models.Protein]
        """
        return {
            protein.hgnc_symbol
            for protein in self.proteins
            if protein.hgnc_symbol
        }

    @property
    def resource_id(self):
        """Return this resource's WikiPathways identifier.

        :rtype: str
        """
        return self.wikipathways_id

    @property
    def url(self):
        """Return a formatted URL for getting information on this resource from WikiPathways.

        :rtype: str
        """
        return 'https://www.wikipathways.org/index.php/Pathway:{}'.format(self.wikipathways_id)


class Protein(Base):
    """A database model for a protein."""

    __tablename__ = PROTEIN_TABLE_NAME

    id = Column(Integer, primary_key=True)

    entrez_id = Column(String(255), doc='entrez id of the protein')
    hgnc_id = Column(String(255), doc='hgnc id of the protein')
    hgnc_symbol = Column(String(255), doc='hgnc symbol of the protein')

    def __repr__(self):  # noqa: D105
        return self.hgnc_id

    def serialize_to_protein_node(self):
        """Serialize this node to a PyBEL data dictionary.

        :rtype: pybel.dsl.protein
        """
        return protein_dsl(
            namespace='hgnc',
            name=self.hgnc_symbol,
            identifier=str(self.hgnc_id)
        )

    def get_pathways_ids(self):
        """Return the pathways associated with the protein.

        :rtype: set[str]
        """
        return {
            pathway.wikipathways_id
            for pathway in self.pathways
        }
