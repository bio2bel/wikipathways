# -*- coding: utf-8 -*-
""" This module contains tests enrichment of BEL graphs using Bio2BEL WikiPathways"""

from tests.constants import DatabaseMixin, enrichment_graph


class TestEnrich(DatabaseMixin):
    """Tests the enrichment of module"""

    def test_get_pathway_graph(self):
        graph = self.manager.get_pathway_graph_by_id('WP3596')

        self.assertEqual(6, graph.number_of_nodes())  # 5 proteins + pathway node
        self.assertEqual(5, graph.number_of_edges())  # 5 edges protein -- pathway

    def test_enrich_wikipathway_pathway(self):
        graph_example = enrichment_graph()

        self.manager.enrich_wikipathways_pathway(graph_example)

        self.assertEqual(6, graph_example.number_of_nodes())  # 4 nodes + 2 new
        self.assertEqual(5, graph_example.number_of_edges())  # 3 + 2 new

    def test_enrich_wikipathway_protein(self):
        graph_example = enrichment_graph()

        self.manager.enrich_wikipathways_protein(graph_example)

        self.assertEqual(6, graph_example.number_of_nodes())  # 4 +  2 new pathways
        self.assertEqual(5, graph_example.number_of_edges())  # 3 + 2 new
