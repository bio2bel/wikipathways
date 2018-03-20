# -*- coding: utf-8 -*-

"""
This module populates the tables of bio2bel_wikipathways
"""

import itertools as itt
import logging
from collections import Counter

from bio2bel.utils import get_connection
from bio2bel_hgnc.manager import Manager as HgncManager
from pybel.constants import PART_OF, FUNCTION, PROTEIN, BIOPROCESS, NAMESPACE, NAME
from pybel.struct.graph import BELGraph
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from .constants import MODULE_NAME, WIKIPATHWAYS
from .models import Base, Pathway, Protein
from .parser import parse_gmt_file

__all__ = [
    'Manager'
]

log = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class Manager(object):
    def __init__(self, connection=None):
        self.connection = get_connection(MODULE_NAME, connection)
        self.engine = create_engine(self.connection)
        self.session_maker = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        self.session = self.session_maker()
        self.create_all()

    def create_all(self, check_first=True):
        """Create tables for Bio2BEL WikiPathways"""
        log.info('create table in {}'.format(self.engine.url))
        Base.metadata.create_all(self.engine, checkfirst=check_first)

    def drop_all(self, check_first=True):
        """Drop tables for Bio2BEL WikiPathways"""
        log.info('drop tables in {}'.format(self.engine.url))
        Base.metadata.drop_all(self.engine, checkfirst=check_first)

    @staticmethod
    def ensure(connection=None):
        """Checks and allows for a Manager to be passed to the function. """
        if connection is None or isinstance(connection, str):
            return Manager(connection=connection)

        if isinstance(connection, Manager):
            return connection

        raise TypeError

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

    def get_pathway_by_name(self, pathway_name):
        """Gets a pathway by its wikipathways id

        :param pathway_name: wikipathways name
        :rtype: Optional[Pathway]
        """
        pathways = self.session.query(Pathway).filter(Pathway.name == pathway_name).all()

        # TODO: There are duplicate pathway names in WikiPathways
        if not pathways:
            return None

        return pathways[0]

    def get_all_pathways(self):
        """Gets all pathways stored in the database

        :rtype: list[Pathway]
        """
        return self.session.query(Pathway).all()

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

        :param hgnc_id: hgnc identifier
        :rtype: Optional[Protein]
        """
        return self.session.query(Protein).filter(Protein.hgnc_symbol == hgnc_symbol).one_or_none()

    def export_genesets(self):
        """Returns pathway - genesets mapping"""
        return {
            pathway.name: {
                protein.hgnc_symbol
                for protein in pathway.proteins
            }
            for pathway in self.session.query(Pathway).all()
        }

    """Methods to populate the DB"""

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
        :return A BEL Graph corresponding to the wikipathway id
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
