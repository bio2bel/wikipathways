# -*- coding: utf-8 -*-
""" This module contains tests for parsing GMT files"""

from bio2bel_wikipathways.models import Pathway, Protein
from tests.constants import DatabaseMixin


class TestParse(DatabaseMixin):
    """Tests the parsing module"""

    def test_pathway_count(self):
        pathway_number = self.manager.session.query(Pathway).count()
        self.assertEqual(5, pathway_number)

    def test_protein_count(self):
        protein_number = self.manager.session.query(Protein).count()
        self.assertEqual(17, protein_number)

    def test_pathway_protein_1(self):
        pathway = self.manager.get_pathway_by_id('WP3596')
        self.assertIsNotNone(pathway, msg='Unable to find pathway')
        self.assertEqual(5, len(pathway.proteins))

    def test_pathway_protein_2(self):
        pathway = self.manager.get_pathway_by_id('WP4022')
        self.assertIsNotNone(pathway, msg='Unable to find pathway')
        self.assertEqual(2, len(pathway.proteins))

    def test_gene_query_1(self):
        """Single protein query. This protein is associated with 1 pathways"""
        enriched_pathways = self.manager.query_gene_set(['MAT2B'])
        self.assertIsNotNone(enriched_pathways, msg='Enriching function is not working')

        self.assertIn('WP2333', enriched_pathways, msg='Keys: {}'.format(enriched_pathways.keys()))

        self.assertEqual(
            {
                "pathway_id": "WP2333",
                "pathway_name": "Trans-sulfuration pathway",
                "mapped_proteins": 1,
                "pathway_size": 3,
                "pathway_gene_set": {'DNMT1', 'MAT2B', 'GCLM'}
            },
            enriched_pathways["WP2333"]
        )

    def test_gene_query_2(self):
        """Multiple protein query"""
        enriched_pathways = self.manager.query_gene_set(['UGT2B7', 'UGT2B4', 'CDKN1A'])
        self.assertIsNotNone(enriched_pathways, msg='Enriching function is not working')

        self.assertEqual(
            {
                "pathway_id": "WP536",
                "pathway_name": "Calcium Regulation in the Cardiac Cell",
                "mapped_proteins": 1,
                "pathway_size": 6,
                "pathway_gene_set": {'MIR6869', 'RGS5', 'UGT2B4', 'GNGT1', 'GNG11', 'KCNJ3'},
            },
            enriched_pathways["WP536"]
        )

        self.assertEqual(
            {
                "pathway_id": "WP1604",
                "pathway_name": "Codeine and Morphine Metabolism",
                "mapped_proteins": 2,
                "pathway_size": 2,
                "pathway_gene_set": {'UGT2B7', 'UGT2B4'}
            },
            enriched_pathways["WP1604"]
        )

        self.assertEqual(
            {
                "pathway_id": "WP3596",
                "pathway_name": "miR-517 relationship with ARCN1 and USP1",
                "mapped_proteins": 1,
                "pathway_size": 5,
                "pathway_gene_set": {'USP1', 'ARCN1', 'CDKN1A', 'ID1', 'ID2'}
            },
            enriched_pathways["WP3596"]
        )

    def test_gene_query_3(self):
        """Multiple protein query"""
        enriched_pathways = self.manager.query_gene_set(['UGT2B7', 'UGT2B4'])
        self.assertIsNotNone(enriched_pathways, msg='Enriching function is not working')

        self.assertEqual(
            {
                "pathway_id": "WP1604",
                "pathway_name": "Codeine and Morphine Metabolism",
                "mapped_proteins": 2,
                "pathway_size": 2,
                "pathway_gene_set": {'UGT2B7', 'UGT2B4'}
            },
            enriched_pathways["WP1604"]
        )

        self.assertEqual(
            {
                "pathway_id": "WP536",
                "pathway_name": "Calcium Regulation in the Cardiac Cell",
                "mapped_proteins": 1,
                "pathway_size": 6,
                "pathway_gene_set": {'MIR6869', 'RGS5', 'UGT2B4', 'GNGT1', 'GNG11', 'KCNJ3'},
            }
            ,
            enriched_pathways["WP536"]
        )
