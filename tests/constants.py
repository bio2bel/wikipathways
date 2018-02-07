# -*- coding: utf-8 -*-
""" This module contains all test constants"""

import os
import pathlib
import tempfile
import unittest

from bio2bel_hgnc.manager import Manager as HgncManager

from bio2bel_wikipathways.manager import Manager
from bio2bel_wikipathways.constants import WIKIPATHWAYS, HGNC

dir_path = os.path.dirname(os.path.realpath(__file__))
resources_path = os.path.join(dir_path, 'resources')

gene_sets_path = os.path.join(resources_path, 'test_gmt_file.gmt')

hgnc_test_path = os.path.join(resources_path, 'hgnc_test.json')
hcop_test_path = os.path.join(resources_path, 'hcop_test.txt')

from pybel.dsl import protein, gene, bioprocess
from pybel.struct.graph import BELGraph
from pybel.constants import *


class DatabaseMixin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Create temporary file"""

        cls.fd, cls.path = tempfile.mkstemp()
        cls.connection = 'sqlite:///' + cls.path

        log.info('Test generated connection string %s', cls.connection)

        # create temporary database
        cls.manager = Manager(cls.connection)

        """HGNC Manager"""

        cls.hgnc_manager = HgncManager(connection=cls.connection)

        cls.hgnc_manager.create_all()

        cls.hgnc_manager.populate(
            hgnc_file_path=hgnc_test_path,
            hcop_file_path=hcop_test_path,
        )

        # fill temporary database with test data
        cls.manager.populate(
            url=pathlib.Path(gene_sets_path).as_uri()
        )

    @classmethod
    def tearDownClass(cls):
        """Closes the connection in the manager and deletes the temporary database"""
        cls.manager.drop_all()
        cls.hgnc_manager.drop_all()
        cls.manager.session.close()
        cls.hgnc_manager.session.close()
        os.close(cls.fd)
        os.remove(cls.path)


protein_a = protein(namespace=HGNC, name='DNMT1')
protein_b = protein(namespace=HGNC, name='POLA1')
gene_c = gene(namespace=HGNC, name='PGLS')
pathway_a = bioprocess(namespace=WIKIPATHWAYS, name='Codeine and Morphine Metabolism')


def enrichment_graph():
    """Simple test graph with 2 proteins, one gene, and one kegg pathway all contained in HGNC"""

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