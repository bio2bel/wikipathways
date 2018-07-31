# -*- coding: utf-8 -*-

"""Test constants for Bio2BEL WikiPathways."""

import logging
import os
import pathlib

from bio2bel.manager.connection_manager import build_engine_session
from bio2bel.testing import TemporaryConnectionMixin
import bio2bel_hgnc
from bio2bel_wikipathways.constants import HGNC, WIKIPATHWAYS
from bio2bel_wikipathways.manager import Manager
import pybel
from pybel.constants import DECREASES, INCREASES, PART_OF, RELATION
from pybel.dsl import bioprocess, gene, protein
from pybel.struct.graph import BELGraph

log = logging.getLogger(__name__)

dir_path = os.path.dirname(os.path.realpath(__file__))
resources_path = os.path.join(dir_path, 'resources')

gene_sets_path = os.path.join(resources_path, 'test_gmt_file.gmt')

hgnc_test_path = os.path.join(resources_path, 'hgnc_test.json')
hcop_test_path = os.path.join(resources_path, 'hcop_test.txt')


class DatabaseMixin(TemporaryConnectionMixin):
    """Load the database before each test."""

    @classmethod
    def setUpClass(cls):
        """Create a temporary file and populate the database."""
        super().setUpClass()

        cls.engine, cls.session = build_engine_session(connection=cls.connection)

        # HGNC manager
        cls.hgnc_manager = bio2bel_hgnc.Manager(engine=cls.engine, session=cls.session)
        cls.hgnc_manager.create_all()
        cls.hgnc_manager.populate(hgnc_file_path=hgnc_test_path, use_hcop=False)

        # create temporary database
        cls.manager = Manager(engine=cls.engine, session=cls.session)

        # fill temporary database with test data
        cls.manager.populate(url=pathlib.Path(gene_sets_path).as_uri())

        # PyBEL manager
        cls.pybel_manager = pybel.Manager(engine=cls.engine, session=cls.session)
        cls.pybel_manager.create_all()

    @classmethod
    def tearDownClass(cls):
        """Close the connection in the manager and deletes the temporary database."""
        cls.session.close()
        super().tearDownClass()


protein_a = protein(namespace=HGNC, name='DNMT1')
protein_b = protein(namespace=HGNC, name='POLA1')
gene_c = gene(namespace=HGNC, name='PGLS')
pathway_a = bioprocess(namespace=WIKIPATHWAYS, name='Codeine and Morphine Metabolism')


def get_enrichment_graph():
    """Build a simple test graph with 2 proteins, one gene, and one kegg pathway all contained in HGNC."""
    graph = BELGraph(
        name='My test graph for enrichment',
        version='0.0.1'
    )

    protein_a_tuple = graph.add_node_from_data(protein_a)
    protein_b_tuple = graph.add_node_from_data(protein_b)
    gene_c_tuple = graph.add_node_from_data(gene_c)
    pathway_a_tuple = graph.add_node_from_data(pathway_a)

    graph.add_edge(protein_a_tuple, protein_b_tuple, attr_dict={
        RELATION: INCREASES,
    })

    graph.add_edge(protein_b_tuple, gene_c_tuple, attr_dict={
        RELATION: DECREASES,
    })

    graph.add_edge(gene_c_tuple, pathway_a_tuple, attr_dict={
        RELATION: PART_OF,
    })

    return graph
