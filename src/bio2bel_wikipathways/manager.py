# -*- coding: utf-8 -*-

"""This module populates the tables of bio2bel_wikipathways."""

import logging

from bio2bel.manager.bel_manager import BELManagerMixin
from bio2bel.manager.flask_manager import FlaskMixin
from bio2bel.manager.namespace_manager import BELNamespaceManagerMixin
import bio2bel_hgnc
from compath_utils import CompathManager
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from pybel.constants import BIOPROCESS, FUNCTION, NAME, NAMESPACE, PROTEIN
from pybel.manager.models import NamespaceEntry
from pybel.struct.graph import BELGraph
from tqdm import tqdm

from .constants import MODULE_NAME, WIKIPATHWAYS
from .models import Base, Pathway, Protein
from .parser import parse_gmt_file

__all__ = [
    'Manager'
]

log = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class Manager(CompathManager, FlaskMixin, BELNamespaceManagerMixin, BELManagerMixin):
    """Bio2BEL Manager for WikiPathways."""

    module_name = MODULE_NAME

    flask_admin_models = [Pathway, Protein]
    namespace_model = pathway_model = Pathway
    pathway_model_identifier_column = Pathway.wikipathways_id
    protein_model = Protein

    identifiers_recommended = 'WikiPathways'
    identifiers_pattern = 'WP\d{1,5}(\_r\d+)?$'
    identifiers_miriam = 'MIR:00000076'
    identifiers_namespace = 'wikipathways'
    identifiers_url = 'http://identifiers.org/wikipathways/'

    @property
    def _base(self):
        return Base

    """Override views in _make_admin"""

    def _add_admin(self, app, **kwargs):
        class PathwayView(ModelView):
            """Pathway view in Flask-admin."""

            column_searchable_list = (
                Pathway.wikipathways_id,
                Pathway.name
            )

        class ProteinView(ModelView):
            """Protein view in Flask-admin."""

            column_searchable_list = (
                Protein.entrez_id,
                Protein.hgnc_symbol,
                Protein.hgnc_id
            )

        admin = Admin(app, **kwargs)
        admin.add_view(PathwayView(Pathway, self.session))
        admin.add_view(ProteinView(Protein, self.session))
        return admin

    def summarize(self):
        """Summarize the database.

        :rtype: dict[str,int]
        """
        return dict(
            pathways=self._count_model(Pathway),
            proteins=self._count_model(Protein),
        )

    def query_pathway_by_name(self, query, limit=None):
        """Return all pathways having the query in their names.

        :param query: query string
        :param Optional[int] limit: limit result query
        :rtype: list[Pathway]
        """
        q = self.session.query(Pathway).filter(Pathway.name.contains(query))

        if limit:
            q = q.limit(limit)

        return q.all()

    def get_or_create_pathway(self, wikipathways_id, name=None):
        """Get an pathway from the database or creates it.

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
        """Get an pathway from the database or creates it.

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
        """Get a protein by its wikipathways id.

        :param entrez_id: entrez identifier
        :rtype: Optional[Protein]
        """
        return self.session.query(Protein).filter(Protein.entrez_id == entrez_id).one_or_none()

    def get_protein_by_hgnc_id(self, hgnc_id):
        """Get a protein by its hgnc_id.

        :param hgnc_id: hgnc_id
        :rtype: Optional[Protein]
        """
        return self.session.query(Protein).filter(Protein.hgnc_id == hgnc_id).one_or_none()

    def get_protein_by_hgnc_symbol(self, hgnc_symbol):
        """Get a protein by its hgnc symbol.

        :param hgnc_symbol: hgnc identifier
        :rtype: Optional[Protein]
        """
        return self.session.query(Protein).filter(Protein.hgnc_symbol == hgnc_symbol).one_or_none()

    """Methods to populate the DB"""

    def populate(self, url=None):
        """Populate the database.

        :param Optional[str] url: url from a GMT file
        """
        hgnc_manager = bio2bel_hgnc.Manager(engine=self.engine, session=self.session)
        if not hgnc_manager.is_populated():
            hgnc_manager.populate()

        pathways = parse_gmt_file(url=url)

        # Dictionaries to map across identifiers
        entrez_to_hgnc_symbol = hgnc_manager.build_entrez_id_symbol_mapping()
        hgnc_symbol_id = hgnc_manager.build_hgnc_symbol_id_mapping()

        entrez_id_protein = {}
        missing_entrez_ids = set()

        for pathway_name, wikipathways_id, gene_set in tqdm(pathways, desc='Loading database'):

            pathway = self.get_or_create_pathway(wikipathways_id=wikipathways_id, name=pathway_name.strip())

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

    def to_bel(self):
        """Return a new graph corresponding to the pathway.

        :param str wikipathways_id: wikipathways identifier
        :rtype: Optional[pybel.BELGraph]
        :return: A BEL Graph corresponding to the wikipathway id

        Example Usage:

        >>> manager = Manager()
        >>> manager.get_pathway_graph_by_id('WP61') # Notch signaling pathway
        """
        graph = BELGraph(
            name='WikiPathways Associations',
            version='1.0.0',
        )

        wikipathways_namespace = self.upload_bel_namespace()
        graph.namespace_url[wikipathways_namespace.keyword] = wikipathways_namespace.url

        hgnc_manager = bio2bel_hgnc.Manager(engine=self.engine, session=self.session)
        hgnc_namespace = hgnc_manager.upload_bel_namespace()
        graph.namespace_url[hgnc_namespace.keyword] = hgnc_namespace.url

        for pathway in tqdm(self.get_all_pathways(), total=self._count_model(Pathway)):
            for protein in pathway.proteins:
                pathway_bel = pathway.serialize_to_pathway_node()
                protein_bel = protein.serialize_to_protein_node()
                graph.add_part_of(protein_bel, pathway_bel)

        return graph

    def get_pathway_graph_by_id(self, wikipathways_id):
        """Return a new graph corresponding to the pathway.

        :param str wikipathways_id: wikipathways identifier
        :rtype: Optional[pybel.BELGraph]
        :return: A BEL Graph corresponding to the wikipathway id

        Example Usage:

        >>> manager = Manager()
        >>> manager.get_pathway_graph_by_id('WP61') # Notch signaling pathway
        """
        pathway = self.get_pathway_by_id(wikipathways_id)

        if pathway is None:
            return

        graph = BELGraph(
            name='{} graph'.format(pathway.name),
            version='1.0.0',
        )

        wikipathways_namespace = self.upload_bel_namespace()
        graph.namespace_url[wikipathways_namespace.keyword] = wikipathways_namespace.url

        hgnc_manager = bio2bel_hgnc.Manager(engine=self.engine, session=self.session)
        hgnc_namespace = hgnc_manager.upload_bel_namespace()
        graph.namespace_url[hgnc_namespace.keyword] = hgnc_namespace.url

        pathway_node = pathway.serialize_to_pathway_node()

        for protein in pathway.proteins:
            graph.add_part_of(protein.serialize_to_protein_node(), pathway_node)

        return graph

    def enrich_wikipathways_pathway(self, graph):
        """Enrich all proteins belonging to wikipathways pathway nodes in the graph.

        :param pybel.BELGraph graph: A BEL Graph
        """
        for node, data in graph.nodes(data=True):
            if data[FUNCTION] == BIOPROCESS and data[NAMESPACE] == WIKIPATHWAYS and NAME in data:
                pathway = self.get_pathway_by_name(data[NAME])
                for protein in pathway.proteins:
                    graph.add_part_of(protein.serialize_to_protein_node(), node)

    def enrich_wikipathways_protein(self, graph):
        """Enrich all wikipathways pathways associated with proteins in the graph.

        :param pybel.BELGraph graph: A BEL Graph
        """
        for node, data in graph.nodes(data=True):
            if data[FUNCTION] == PROTEIN and data[NAMESPACE] == 'HGNC':
                protein = self.get_protein_by_hgnc_symbol(data[NAME])
                for pathway in protein.pathways:
                    graph.add_part_of(node, pathway.serialize_to_pathway_node())

    def _create_namespace_entry_from_model(self, model, namespace):
        """Create a namespace entry from the model.

        :param Pathway model: The model to convert
        :type namespace: pybel.manager.models.Namespace
        :rtype: Optional[pybel.manager.models.NamespaceEntry]
        """
        return NamespaceEntry(encoding='B', name=model.name, identifier=model.wikipathways_id, namespace=namespace)

    @staticmethod
    def _get_identifier(model):
        """Extract the identifier from a pathway mode.

        :param Pathway model: The model to convert
        :rtype: str
        """
        return model.wikipathways_id
