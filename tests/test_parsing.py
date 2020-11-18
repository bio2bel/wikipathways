# -*- coding: utf-8 -*-

"""Tests for Bio2BEL WikiPathways."""

from bio2bel_wikipathways.models import Pathway, Protein
from pybel import BELGraph, dsl
from pybel.language import Entity
from tests.constants import DatabaseMixin, get_enrichment_graph


class TestParse(DatabaseMixin):
    """Tests the parsing module."""

    def test_pathway_count(self):
        """Test the correct number of pathways were populated."""
        pathway_number = self.wikipathways_manager.session.query(Pathway).count()
        self.assertEqual(5, pathway_number)

    def test_protein_count(self):
        """Test the correct number of proteins were populated."""
        protein_number = self.wikipathways_manager.session.query(Protein).count()
        self.assertEqual(17, protein_number)

    def test_pathway_protein_1(self):
        """Test that pathway WP3596 can be retrieved by identifier."""
        pathway = self.wikipathways_manager.get_pathway_by_id('WP3596')
        self.assertIsNotNone(pathway, msg='Unable to find pathway')
        self.assertEqual(5, len(pathway.proteins))

    def test_pathway_protein_2(self):
        """Test that pathway WP4022 can be retrieved by identifier."""
        pathway = self.wikipathways_manager.get_pathway_by_id('WP4022')
        self.assertIsNotNone(pathway, msg='Unable to find pathway')
        self.assertEqual(2, len(pathway.proteins))

    def test_gene_query_1(self):
        """Test a single protein query for a protein that is associated with 1 pathway."""
        enriched_pathways = self.wikipathways_manager.query_hgnc_symbols(['MAT2B'])
        self.assertIsNotNone(enriched_pathways, msg='Enriching function is not working')

        self.assertIn('WP2333', enriched_pathways, msg=f'Keys: {enriched_pathways.keys()}')

        self.assertEqual(
            {
                "pathway_id": "WP2333",
                "pathway_name": "Trans-sulfuration pathway",
                "mapped_proteins": 1,
                "pathway_size": 3,
                "pathway_gene_set": {'DNMT1', 'MAT2B', 'GCLM'},
            },
            enriched_pathways["WP2333"],
        )

    def test_gene_query_2(self):
        """Test a multiple protein query."""
        enriched_pathways = self.wikipathways_manager.query_hgnc_symbols(['UGT2B7', 'UGT2B4', 'CDKN1A'])
        self.assertIsNotNone(enriched_pathways, msg='Enriching function is not working')

        self.assertEqual(
            {
                "pathway_id": "WP536",
                "pathway_name": "Calcium Regulation in the Cardiac Cell",
                "mapped_proteins": 1,
                "pathway_size": 6,
                "pathway_gene_set": {'MIR6869', 'RGS5', 'UGT2B4', 'GNGT1', 'GNG11', 'KCNJ3'},
            },
            enriched_pathways["WP536"],
        )

        self.assertEqual(
            {
                "pathway_id": "WP1604",
                "pathway_name": "Codeine and Morphine Metabolism",
                "mapped_proteins": 2,
                "pathway_size": 2,
                "pathway_gene_set": {'UGT2B7', 'UGT2B4'},
            },
            enriched_pathways["WP1604"],
        )

        self.assertEqual(
            {
                "pathway_id": "WP3596",
                "pathway_name": "miR-517 relationship with ARCN1 and USP1",
                "mapped_proteins": 1,
                "pathway_size": 5,
                "pathway_gene_set": {'USP1', 'ARCN1', 'CDKN1A', 'ID1', 'ID2'},
            },
            enriched_pathways["WP3596"],
        )

    def test_gene_query_3(self):
        """Test a multiple protein query."""
        enriched_pathways = self.wikipathways_manager.query_hgnc_symbols(['UGT2B7', 'UGT2B4'])
        self.assertIsNotNone(enriched_pathways, msg='Enriching function is not working')

        self.assertEqual(
            {
                "pathway_id": "WP1604",
                "pathway_name": "Codeine and Morphine Metabolism",
                "mapped_proteins": 2,
                "pathway_size": 2,
                "pathway_gene_set": {'UGT2B7', 'UGT2B4'},
            },
            enriched_pathways["WP1604"],
        )

        self.assertEqual(
            {
                "pathway_id": "WP536",
                "pathway_name": "Calcium Regulation in the Cardiac Cell",
                "mapped_proteins": 1,
                "pathway_size": 6,
                "pathway_gene_set": {'MIR6869', 'RGS5', 'UGT2B4', 'GNGT1', 'GNG11', 'KCNJ3'},
            },
            enriched_pathways["WP536"],
        )

    def test_get_pathway_graph(self):
        """Test getting a pathway graph."""
        graph = self.wikipathways_manager.get_pathway_graph('WP3596')

        self.assertEqual(6, graph.number_of_nodes())  # 5 proteins + pathway node
        self.assertEqual(5, graph.number_of_edges())  # 5 edges protein -- pathway

    def test_enrich_wikipathway_pathway(self):
        """Test enriching protein members of a WikiPathway node."""
        graph_example = get_enrichment_graph()

        self.wikipathways_manager.enrich_pathways(graph_example)

        self.assertEqual(6, graph_example.number_of_nodes())  # 4 nodes + 2 new
        self.assertEqual(5, graph_example.number_of_edges())  # 3 + 2 new

    def test_enrich_wikipathway_protein(self):
        """Test enriching pathway memberships of a protein."""
        self.assertNotEqual(0, self.wikipathways_manager.count_proteins())
        self.assertNotEqual(0, self.wikipathways_manager.count_pathways())

        graph = BELGraph()
        pathway_1 = dsl.BiologicalProcess(
            namespace='wikipathways', identifier='WP1604', name='Codeine and Morphine Metabolism',
        )
        pathway_2 = dsl.BiologicalProcess(
            namespace='wikipathways', identifier='WP536', name='Calcium Regulation in the Cardiac Cell',
        )
        protein_1 = dsl.Protein(
            namespace='hgnc',
            identifier='12553',
            name='UGT2B4',
            xrefs=[Entity(namespace='ncbigene', identifier='7363')],
        )
        protein_2 = dsl.Protein(
            namespace='hgnc',
            identifier='12554',
            name='UGT2B7',
            xrefs=[Entity(namespace='ncbigene', identifier='7363')],
        )

        hgnc_ids = {protein_1.identifier, protein_2.identifier}
        for hgnc_id in hgnc_ids:
            self.assertIsNotNone(
                self.wikipathways_manager.get_protein_by_hgnc_id(hgnc_id),
                msg=f'IDs available: {",".join(p.hgnc_id for p in self.wikipathways_manager.list_proteins())}',
            )

        proteins = self.wikipathways_manager.get_proteins_by_hgnc_ids(hgnc_ids)
        self.assertEqual(2, len(proteins))

        pathways = self.wikipathways_manager.get_pathways_by_hgnc_ids(hgnc_ids)
        self.assertEqual(2, len(pathways), msg=', '.join(map(repr, pathways)))

        graph.add_node_from_data(protein_1)
        graph.add_node_from_data(protein_2)

        self.wikipathways_manager.enrich_proteins(graph)

        self.assertEqual(
            {
                pathway_1,
                protein_1,
                protein_2,
                pathway_2,
                dsl.Protein(namespace='hgnc', identifier='6264', name='KCNJ3'),
                dsl.Protein(namespace='hgnc', identifier='4403', name='GNG11'),
                dsl.Protein(namespace='hgnc', identifier='4411', name='GNGT1'),
                dsl.Protein(namespace='hgnc', identifier='10001', name='RGS5'),
                dsl.Protein(namespace='hgnc', identifier='50056', name='MIR6869'),
            },
            set(graph),
            msg='Wrong nodes in graph',
        )
        self.assertEqual(8, graph.number_of_edges())
