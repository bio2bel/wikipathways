# -*- coding: utf-8 -*-

"""Test constants for Bio2BEL WikiPathways."""

import logging
import os

import bio2bel_wikipathways
import bio2bel_wikipathways.manager
import pybel
from bio2bel.manager.connection_manager import build_engine_session
from bio2bel.testing import TemporaryConnectionMixin
from bio2bel_wikipathways.constants import HGNC, WIKIPATHWAYS
from pybel.dsl import BiologicalProcess, Gene, Protein
from pybel.struct.graph import BELGraph
from pyobo.mocks import _replace_mapping_getter

logger = logging.getLogger(__name__)

dir_path = os.path.dirname(os.path.realpath(__file__))
resources_path = os.path.join(dir_path, 'resources')

gene_sets_path = os.path.join(resources_path, 'test_gmt_file.gmt')

mock_name_id_mapping = _replace_mapping_getter('bio2bel_wikipathways.manager.get_name_id_mapping', {
    'ncbitaxon': {
        'Homo sapiens': '9606',
    },
})


class DatabaseMixin(TemporaryConnectionMixin):
    """Load the database before each test."""

    wikipathways_manager: bio2bel_wikipathways.Manager
    pybel_manager = pybel.Manager

    @classmethod
    def setUpClass(cls):
        """Create a temporary file and populate the database."""
        super().setUpClass()

        cls.engine, cls.session = build_engine_session(connection=cls.connection)

        # WikiPathways manager
        cls.wikipathways_manager = bio2bel_wikipathways.Manager(engine=cls.engine, session=cls.session)
        with mock_name_id_mapping:
            if 1 != len(bio2bel_wikipathways.manager.get_name_id_mapping('ncbitaxon')):
                raise ValueError('mock did not work properly')
            cls.wikipathways_manager.populate(paths={'9606': gene_sets_path})

        # PyBEL manager
        cls.pybel_manager = pybel.Manager(engine=cls.engine, session=cls.session)
        cls.pybel_manager.create_all()

    @classmethod
    def tearDownClass(cls):
        """Close the connection in the manager and deletes the temporary database."""
        cls.session.close()
        super().tearDownClass()


protein_a = Protein(namespace=HGNC, identifier='2976', name='DNMT1')
protein_b = Protein(namespace=HGNC, identifier='9173', name='POLA1')
gene_c = Gene(namespace=HGNC, identifier='8903', name='PGLS')
pathway_a = BiologicalProcess(namespace=WIKIPATHWAYS, identifier='WP1604', name='Codeine and Morphine Metabolism')


def get_enrichment_graph():
    """Build a simple test graph with 2 proteins, one gene, and one pathway all contained in HGNC."""
    graph = BELGraph(
        name='My test graph for enrichment',
        version='0.0.1',
    )
    graph.add_increases(protein_a, protein_b, citation='1234', evidence='')
    graph.add_decreases(protein_b, gene_c, citation='1234', evidence='')
    graph.add_part_of(gene_c, pathway_a)
    return graph
