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
