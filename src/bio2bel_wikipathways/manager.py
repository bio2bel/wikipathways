# -*- coding: utf-8 -*-

"""
This module populates the tables of bio2bel_wikipathways
"""

import itertools as itt
import logging
from collections import Counter

from bio2bel_hgnc.manager import Manager as HgncManager
from pybel.constants import BIOPROCESS, FUNCTION, NAME, NAMESPACE, PART_OF, PROTEIN
from pybel.struct.graph import BELGraph
from tqdm import tqdm

from bio2bel import bio2bel_populater
from compath_utils import CompathManager
from .constants import MODULE_NAME, WIKIPATHWAYS
from .models import Base, Pathway, Protein
from .parser import parse_gmt_file

__all__ = [
    'Manager'
]

log = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class Manager(CompathManager):
    module_name = MODULE_NAME
    flask_admin_models = [Pathway, Protein]
    pathway_model = Pathway

    @property
    def base(self):
        return Base

    """Override views in _make_admin"""

    def _add_admin(self, app, **kwargs):
        from flask_admin.contrib.sqla import ModelView
        from flask_admin import Admin

        class PathwayView(ModelView):
            """Pathway view in Flask-admin"""
            column_searchable_list = (
                Pathway.wikipathways_id,
                Pathway.name
            )

        class ProteinView(ModelView):
            """Protein view in Flask-admin"""
            column_searchable_list = (
                Protein.entrez_id,
                Protein.hgnc_symbol,
                Protein.hgnc_id
            )

        admin = Admin(app, **kwargs)
        admin.add_view(PathwayView(Pathway, self.session))
        admin.add_view(ProteinView(Protein, self.session))
        return admin

    """Custom query methods"""

    def query_gene_set(self, gene_set):
        """Returns pathway counter dictionary

        :param list[str] gene_set: gene set to be queried
        :rtype: dict[str,dict]]
        :return: Enriched pathways with pathway info and mapped pathways/total
        """
        proteins = self._query_proteins_in_hgnc_list(gene_set)

        pathways_lists = [
            protein.get_pathways_ids()
            for protein in proteins
        ]

        # Flat the pathways lists and applies Counter to get the number matches in every mapped pathway
        pathway_counter = Counter(itt.chain(*pathways_lists))

        enrichment_results = dict()

        for pathway_wikipathways_id, proteins_mapped in pathway_counter.items():
            pathway = self.get_pathway_by_id(pathway_wikipathways_id)

            pathway_gene_set = pathway.get_gene_set()  # Pathway gene set

            enrichment_results[pathway.wikipathways_id] = {
                "pathway_id": pathway.wikipathways_id,
                "pathway_name": pathway.name,
                "mapped_proteins": proteins_mapped,
                "pathway_size": len(pathway_gene_set),
                "pathway_gene_set": pathway_gene_set,
            }

        return enrichment_results

    def _query_proteins_in_hgnc_list(self, gene_set):
        """Returns the proteins in the database within the gene set query

        :param list[str] gene_set: hgnc symbol lists
        :rtype: list[bio2bel_wikipathways.models.Protein]
        :return: list of proteins
        """
        return self.session.query(Protein).filter(Protein.hgnc_symbol.in_(gene_set)).all()

    def get_pathway_by_id(self, wikipathways_id):
        """Gets a pathway by its wikipathways id

        :param wikipathways_id: wikipathways identifier
        :rtype: Optional[Pathway]
        """
        return self.session.query(Pathway).filter(Pathway.wikipathways_id == wikipathways_id).one_or_none()

    def get_pathway_names_to_ids(self):
        """Returns a dictionary of pathway names to ids

        :rtype: dict[str,str]
        """
        human_pathways = self.get_all_pathways()

        return {
            pathway.name: pathway.wikipathways_id
            for pathway in human_pathways
        }

    def get_all_hgnc_symbols(self):
        """Returns the set of genes present in all WikiPathways Pathways

        :rtype: set
        """
        return {
            gene.hgnc_symbol
            for pathway in self.get_all_pathways()
            for gene in pathway.proteins
            if pathway.proteins
        }

    def get_pathway_size_distribution(self):
        """Returns pathway sizes

        :rtype: dict
        :return: pathway sizes
        """

        pathways = self.get_all_pathways()

        return {
            pathway.name: len(pathway.proteins)
            for pathway in pathways
            if pathway.proteins
        }

    def get_gene_distribution(self):
        """Returns the proteins in the database within the gene set query

        :rtype: dict
        :return: pathway sizes
        """

        gene_counter = Counter()

        for pathway in self.get_all_pathways():
            if not pathway.proteins:
                continue

            for gene in pathway.proteins:
                gene_counter[gene.hgnc_symbol] += 1

        return gene_counter

    def query_pathway_by_name(self, query, limit=None):
        """Returns all pathways having the query in their names

        :param query: query string
        :param Optional[int] limit: limit result query
        :rtype: list[Pathway]
        """

        q = self.session.query(Pathway).filter(Pathway.name.contains(query))

        if limit:
            q = q.limit(limit)

        return q.all()

    def get_or_create_pathway(self, wikipathways_id, name=None):
        """Gets an pathway from the database or creates it

        :param str wikipathways_id: wikipathways identifier
        :param Optional[str] name: name of the pathway
        :rtype: Pathway
        """
        pathway = self.get_pathway_by_id(wikipathways_id)

        if pathway is None:
            pathway = Pathway(
                wikipathways_id=wikipathways_id,
                name=name
            )
            self.session.add(pathway)

        return pathway

    def get_or_create_protein(self, entrez_id, hgnc_symbol, hgnc_id):
        """Gets an pathway from the database or creates it

        :param str entrez_id: entrez identifier
        :param str hgnc_symbol: hgnc symbol
        :param str hgnc_id: hgnc identifier
        :rtype: Protein
        """
        protein = self.get_protein_by_entrez_id(entrez_id)

        if protein is None:
            protein = Protein(
                entrez_id=entrez_id,
                hgnc_symbol=hgnc_symbol,
                hgnc_id=hgnc_id
            )

            self.session.add(protein)

        return protein

    def get_protein_by_entrez_id(self, entrez_id):
        """Gets a protein by its wikipathways id

        :param entrez_id: entrez identifier
        :rtype: Optional[Protein]
        """
        return self.session.query(Protein).filter(Protein.entrez_id == entrez_id).one_or_none()

    def get_protein_by_hgnc_id(self, hgnc_id):
        """Gets a protein by its hgnc_id

        :param hgnc_id: hgnc_id
        :rtype: Optional[Protein]
        """
        return self.session.query(Protein).filter(Protein.hgnc_id == hgnc_id).one_or_none()

    def get_protein_by_hgnc_symbol(self, hgnc_symbol):
        """Gets a protein by its hgnc symbol

        :param hgnc_symbol: hgnc identifier
        :rtype: Optional[Protein]
        """
        return self.session.query(Protein).filter(Protein.hgnc_symbol == hgnc_symbol).one_or_none()

    """Methods to populate the DB"""

    @bio2bel_populater(MODULE_NAME)
    def populate(self, url=None):
        """Populates all tables

        :param Optional[str] url: url from gmt file
        """

        pathways = parse_gmt_file(url=url)

        log.info('connecting to HGNC Manager: {}'.format(self.connection))

        hgnc_manager = HgncManager(connection=self.connection)

        # Dictionaries to map across identifiers
        entrez_to_hgnc_symbol = hgnc_manager.build_entrez_id_symbol_mapping()
        hgnc_symbol_id = hgnc_manager.build_hgnc_symbol_id_mapping()

        entrez_id_protein = {}

        missing_entrez_ids = set()

        for pathway_name, wikipathways_id, gene_set in tqdm(pathways, desc='Loading database'):

            pathway = self.get_or_create_pathway(wikipathways_id=wikipathways_id, name=pathway_name)

            for entrez_id in gene_set:

                if entrez_id in entrez_id_protein:
                    protein = entrez_id_protein[entrez_id]

                else:
                    hgnc_symbol = entrez_to_hgnc_symbol.get(entrez_id)

                    if not hgnc_symbol:
                        log.warning("{} ENTREZ ID has no HGNC symbol".format(entrez_id))
                        missing_entrez_ids.add(entrez_id)
                        continue

                    protein = self.get_or_create_protein(entrez_id, hgnc_symbol, hgnc_symbol_id[hgnc_symbol])
                    entrez_id_protein[entrez_id] = protein

                if pathway not in protein.pathways:
                    protein.pathways.append(pathway)

            self.session.commit()

        if missing_entrez_ids:
            log.warning("Total of {} missing ENTREZ".format(len(missing_entrez_ids)))

    """Methods to enrich BEL graphs"""

    def get_pathway_graph_by_id(self, wikipathways_id):
        """Returns a new graph corresponding to the pathway

        :param str wikipathways_id: wikipathways identifier
        :rtype: pybel.BELGraph
        :return: A BEL Graph corresponding to the wikipathway id
        """

        pathway = self.get_pathway_by_id(wikipathways_id)

        graph = BELGraph(
            name='{} graph'.format(pathway.name),
        )

        pathway_node = pathway.serialize_to_pathway_node()

        for protein in pathway.proteins:
            graph.add_qualified_edge(
                pathway_node,
                protein.serialize_to_protein_node(),
                relation=PART_OF,
                citation='27899662',
                evidence='http://www.genome.jp/wikipathways/'
            )

        return graph

    def enrich_wikipathways_pathway(self, graph):
        """Enrich all proteins belonging to wikipathways pathway nodes in the graph

        :param graph: A BEL Graph
        :type graph: pybel.BELGraph
        :rtype: pybel.BELGraph
        :return A BEL Graph
        """

        for node, data in graph.nodes(data=True):

            if data[FUNCTION] == BIOPROCESS and data[NAMESPACE] == WIKIPATHWAYS and NAME in data:

                pathway = self.get_pathway_by_name(data[NAME])

                for protein in pathway.proteins:
                    graph.add_qualified_edge(
                        protein.serialize_to_protein_node(),
                        node,
                        relation=PART_OF,
                        citation='27899662',
                        evidence='http://www.genome.jp/wikipathways/'
                    )

        return graph

    def enrich_wikipathways_protein(self, graph):
        """Enrich all wikipathways pathways associated with proteins in the graph

        :param graph: A BEL Graph
        :type graph: pybel.BELGraph
        :rtype: pybel.BELGraph
        :return A BEL Graph
        """

        for node, data in graph.nodes(data=True):

            if data[FUNCTION] == PROTEIN and data[NAMESPACE] == 'HGNC':

                protein = self.get_protein_by_hgnc_symbol(data[NAME])

                for pathway in protein.pathways:
                    graph.add_qualified_edge(
                        node,
                        pathway.serialize_to_pathway_node(),
                        relation=PART_OF,
                        citation='26481357',
                        evidence='https://www.wikipathways.org/index.php/Download_Pathways'
                    )

        return graph
