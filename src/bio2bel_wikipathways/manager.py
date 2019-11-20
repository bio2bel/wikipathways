# -*- coding: utf-8 -*-

"""This module populates the tables of bio2bel_wikipathways."""

import logging
import sys
from typing import Iterable, List, Mapping, Optional, Union

import click
from tqdm import tqdm

import bio2bel_hgnc
from bio2bel.manager.bel_manager import BELManagerMixin
from bio2bel.manager.flask_manager import FlaskMixin
from bio2bel.manager.namespace_manager import BELNamespaceManagerMixin
from compath_utils import CompathManager
from pybel.constants import BIOPROCESS, NAME, PROTEIN
from pybel.manager.models import Namespace, NamespaceEntry
from pybel.struct.graph import BELGraph
from .constants import MODULE_NAME, WIKIPATHWAYS
from .models import Base, Pathway, Protein, protein_pathway
from .parser import parse_gmt_file

__all__ = [
    'Manager',
]

log = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class Manager(CompathManager, BELNamespaceManagerMixin, BELManagerMixin, FlaskMixin):
    """Protein-pathway memberships."""

    module_name = MODULE_NAME
    _base = Base
    edge_model = protein_pathway
    flask_admin_models = [Pathway, Protein]
    namespace_model = pathway_model = Pathway
    pathway_model_identifier_column = Pathway.wikipathways_id
    protein_model = Protein

    identifiers_recommended = 'WikiPathways'
    identifiers_pattern = r'WP\d{1,5}(\_r\d+)?$'
    identifiers_miriam = 'MIR:00000076'
    identifiers_namespace = 'wikipathways'
    identifiers_url = 'http://identifiers.org/wikipathways/'

    """Override views in _make_admin"""

    def _add_admin(self, app, **kwargs):
        from flask_admin import Admin
        from flask_admin.contrib.sqla import ModelView

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

    def summarize(self) -> Mapping[str, int]:
        """Summarize the database."""
        return dict(
            pathways=self._count_model(Pathway),
            proteins=self._count_model(Protein),
        )

    def query_pathway_by_name(self, query: str, limit: Optional[int] = None) -> List[Pathway]:
        """Return all pathways having the query in their names.

        :param query: query string
        :param limit: limit result query
        """
        q = self.session.query(Pathway).filter(Pathway.name.contains(query))

        if limit:
            q = q.limit(limit)

        return q.all()

    def get_or_create_pathway(
            self,
            wikipathways_id: str,
            name: Optional[str] = None,
            species: Optional[str] = None,
    ) -> Pathway:
        """Get an pathway from the database or creates it.

        :param wikipathways_id: WikiPathways identifier
        :param name: name of the pathway
        :param species: species in which the pathway was described
        """
        pathway = self.get_pathway_by_id(wikipathways_id)

        if pathway is None:
            pathway = Pathway(
                wikipathways_id=wikipathways_id,
                name=name,
                species=species,
            )
            self.session.add(pathway)

        return pathway

    def get_or_create_protein(self, entrez_id: str, hgnc_symbol: str, hgnc_id: str) -> Protein:
        """Get an pathway from the database or creates it.

        :param entrez_id: entrez identifier
        :param hgnc_symbol: hgnc symbol
        :param hgnc_id: hgnc identifier
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

    def get_protein_by_entrez_id(self, entrez_id: str) -> Optional[Protein]:
        """Get a protein by its Entrez gene identifier."""
        return self.session.query(Protein).filter(Protein.entrez_id == entrez_id).one_or_none()

    def get_protein_by_hgnc_id(self, hgnc_id: str) -> Optional[Protein]:
        """Get a protein by its HGNC identifier."""
        return self.session.query(Protein).filter(Protein.hgnc_id == hgnc_id).one_or_none()

    def get_protein_by_hgnc_symbol(self, hgnc_symbol: str) -> Optional[Protein]:
        """Get a protein by its HGNC gene symbol."""
        return self.session.query(Protein).filter(Protein.hgnc_symbol == hgnc_symbol).one_or_none()

    """Methods to populate the DB"""

    def populate(self, url: Union[None, str, Iterable[str]] = None):
        """Populate the database.

        :param url: url from a GMT file
        """
        hgnc_manager = bio2bel_hgnc.Manager(engine=self.engine, session=self.session)
        if not hgnc_manager.is_populated():
            hgnc_manager.populate()

        if url is None or isinstance(url, str):
            pathways = parse_gmt_file(url=url)
        elif isinstance(url, Iterable):
            pathways = [
                pathway
                for u in url
                for pathway in parse_gmt_file(url=u)
            ]
        else:
            raise TypeError(f'Invalid type for url: {type(url)} ({url})')

        # Dictionaries to map across identifiers
        entrez_to_hgnc_symbol = hgnc_manager.build_entrez_id_symbol_mapping()
        hgnc_symbol_id = hgnc_manager.build_hgnc_symbol_id_mapping()

        entrez_id_protein = {}
        missing_entrez_ids = set()

        it = tqdm(pathways, desc='Loading WikiPathways')
        for pathway_name, species, wikipathways_id, gene_set in it:
            pathway = self.get_or_create_pathway(
                wikipathways_id=wikipathways_id,
                name=pathway_name.strip(),
                species=species,
            )

            for entrez_id in gene_set:
                if entrez_id in entrez_id_protein:
                    protein = entrez_id_protein[entrez_id]

                else:
                    hgnc_symbol = entrez_to_hgnc_symbol.get(entrez_id)

                    if not hgnc_symbol:
                        it.write(f"({species}) ncbigene:{entrez_id} has no HGNC symbol")
                        missing_entrez_ids.add(entrez_id)
                        continue

                    protein = self.get_or_create_protein(entrez_id, hgnc_symbol, hgnc_symbol_id[hgnc_symbol])
                    entrez_id_protein[entrez_id] = protein

                if pathway not in protein.pathways:
                    protein.pathways.append(pathway)

            self.session.commit()

        if missing_entrez_ids:
            log.warning("Total of {} missing ENTREZ".format(len(missing_entrez_ids)))

    @classmethod
    def _cli_add_populate(cls, main: click.Group) -> click.Group:
        @main.command()
        @click.option('--reset', is_flag=True, help='Nuke database first')
        @click.option('--force', is_flag=True, help='Force overwrite if already populated')
        @click.option('-u', '--url', multiple=True, help='URL of WikiPathways GMT files')
        @click.pass_obj
        def populate(manager: Manager, reset, force, url):
            """Populate the database."""
            if reset:
                click.echo('Deleting the previous instance of the database')
                manager.drop_all()
                click.echo('Creating new models')
                manager.create_all()

            if manager.is_populated() and not force:
                click.echo('Database already populated. Use --force to overwrite')
                sys.exit(0)

            manager.populate(url=url)

        return main

    """Methods to enrich BEL graphs"""

    def to_bel(self) -> BELGraph:
        """Return a new graph corresponding to the pathway.

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

    def get_pathway_graph_by_id(self, wikipathways_id: str) -> Optional[BELGraph]:
        """Return a new graph corresponding to the pathway.

        :param wikipathways_id: WikiPathways identifier
        :return: A BEL Graph corresponding to the WikiPathways identifier

        Example Usage:

        >>> manager = Manager()
        >>> manager.get_pathway_graph_by_id('WP61') # Notch signaling pathway
        """
        pathway = self.get_pathway_by_id(wikipathways_id)

        if pathway is None:
            return

        graph = BELGraph(
            name=f'{pathway.name} ({pathway.species})',
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

    def enrich_wikipathways_pathway(self, graph: BELGraph) -> None:
        """Enrich all proteins belonging to WikiPathways pathway nodes in the graph."""
        for node in list(graph):
            if node.function == BIOPROCESS and node.namespace == WIKIPATHWAYS and node.name:
                pathway = self.get_pathway_by_name(node.name)
                for protein in pathway.proteins:
                    graph.add_part_of(protein.serialize_to_protein_node(), node)

    def enrich_wikipathways_protein(self, graph: BELGraph) -> None:
        """Enrich all WikiPathways pathways associated with proteins in the graph."""
        for node in list(graph):
            if node.function == PROTEIN and node.namespace and node.namespace == 'HGNC':
                protein = self.get_protein_by_hgnc_symbol(node.name)
                for pathway in protein.pathways:
                    graph.add_part_of(node, pathway.serialize_to_pathway_node())

    def _create_namespace_entry_from_model(self, model: Pathway, namespace: Namespace) -> NamespaceEntry:
        """Create a namespace entry from the model."""
        return NamespaceEntry(encoding='B', name=model.name, identifier=model.wikipathways_id, namespace=namespace)

    @staticmethod
    def _get_identifier(model: Pathway) -> str:
        """Extract the identifier from a pathway mode."""
        return model.wikipathways_id
