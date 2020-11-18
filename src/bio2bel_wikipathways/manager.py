# -*- coding: utf-8 -*-

"""This module populates the tables of bio2bel_wikipathways."""

import logging
import sys
from typing import List, Mapping, Optional

import click
from flask_admin.contrib.sqla import ModelView
from tqdm import tqdm

from bio2bel.compath import CompathManager
from pyobo import get_filtered_xrefs, get_id_name_mapping, get_name_id_mapping
from pyobo.cli_utils import verbose_option
from pyobo.sources.wikipathways import parse_wikipathways_gmt
from .constants import MODULE_NAME, SPECIES_REMAPPING, infos
from .models import Base, Pathway, Protein, Species, protein_pathway

__all__ = [
    'Manager',
]

logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class PathwayView(ModelView):
    """Pathway view in Flask-admin."""

    column_searchable_list = (
        Pathway.identifier,
        Pathway.name,
    )


class ProteinView(ModelView):
    """Protein view in Flask-admin."""

    column_searchable_list = (
        Protein.entrez_id,
        Protein.hgnc_symbol,
        Protein.hgnc_id,
    )


class Manager(CompathManager):
    """Protein-pathway memberships."""

    module_name = MODULE_NAME
    _base = Base
    edge_model = protein_pathway
    flask_admin_models = [
        (Pathway, PathwayView),
        (Protein, ProteinView),
        Species,
    ]
    namespace_model = pathway_model = Pathway
    protein_model = Protein

    identifiers_recommended = 'WikiPathways'
    identifiers_pattern = r'WP\d{1,5}(\_r\d+)?$'  # noqa:FS003
    identifiers_miriam = 'MIR:00000076'
    identifiers_namespace = 'wikipathways'
    identifiers_url = 'http://identifiers.org/wikipathways/'

    def summarize(self) -> Mapping[str, int]:
        """Summarize the database."""
        return {
            'pathways': self._count_model(Pathway),
            'proteins': self._count_model(Protein),
            'species': self._count_model(Species),
        }

    def get_or_create_pathway(
        self,
        *,
        identifier: str,
        species: Species,
        revision: str,
        name: Optional[str] = None,
        proteins: Optional[List[Protein]] = None,
    ) -> Pathway:
        """Get an pathway from the database or creates it.

        :param identifier: WikiPathways identifier
        :param name: name of the pathway
        :param species: species in which the pathway was described
        :param revision: the WikiPathways revision number
        :param proteins: A list of proteins to add to the pathway
        """
        pathway = self.get_pathway_by_id(identifier)

        if pathway is None:
            pathway = Pathway(
                identifier=identifier,
                name=name,
                species=species,
                revision=revision,
                proteins=proteins or [],
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
                hgnc_id=hgnc_id,
            )
            self.session.add(protein)

        return protein

    def get_protein_by_entrez_id(self, entrez_id: str) -> Optional[Protein]:
        """Get a protein by its Entrez gene identifier."""
        return self.session.query(Protein).filter(Protein.entrez_id == entrez_id).one_or_none()

    def populate(self, paths: Optional[Mapping[str, str]] = None):
        """Populate the database.

        :param paths: mapping from tax identifiers to paths to GMT files
        """
        if not paths:
            logger.info('No paths given.')
            paths = {info.taxonomy_id: info.path for info in infos.values()}
            logger.info(f'Using default paths at {paths}.')
        elif not isinstance(paths, dict):
            raise TypeError('Invalid type for paths. Shoudl be dict.')

        pathways = [
            pathway
            for taxonomy_id, path in paths.items()
            for pathway in parse_wikipathways_gmt(path)
        ]

        versions = {
            version
            for _identifier, version, _revision, _name, _species_name, _entries in pathways
        }
        if len(versions) != 1:
            raise ValueError('got multiple versions')
        version = list(versions)[0]

        taxonomy_name_to_id = get_name_id_mapping('ncbitaxon')
        species_names = {
            SPECIES_REMAPPING.get(species_name, species_name)
            for _identifier, _version, _revision, _name, species_name, _entries in pathways
        }
        species_name_to_species = {}
        for species_name in tqdm(species_names, desc=f'v{version} serializing species'):
            taxonomy_id = taxonomy_name_to_id[species_name]
            species = species_name_to_species[species_name] = Species(taxonomy_id=taxonomy_id, name=species_name)
            self.session.add(species)

        hgnc_id_to_entrez_id = get_filtered_xrefs('hgnc', 'ncbigene')
        if not hgnc_id_to_entrez_id:
            raise ValueError('Mappings from hgnc to ncbigene couldnt be loaded')

        entrez_id_to_hgnc_id = {v: k for k, v in hgnc_id_to_entrez_id.items()}
        hgnc_id_to_name = get_id_name_mapping('hgnc')

        missing_entrez_ids = set()
        entrez_ids = {
            entrez_id
            for _identifier, _version, _revision, _name, _species, entrez_ids in pathways
            for entrez_id in entrez_ids
        }
        entrez_id_protein = {}
        for entrez_id in tqdm(entrez_ids, desc=f'v{version} serializing proteins'):
            hgnc_id = entrez_id_to_hgnc_id.get(entrez_id)
            if hgnc_id:
                hgnc_symbol = hgnc_id_to_name[hgnc_id]
            else:
                hgnc_symbol = None

            if not hgnc_symbol:
                logging.debug(f"ncbigene:{entrez_id} has no HGNC identifier")
                missing_entrez_ids.add(entrez_id)

            entrez_id_protein[entrez_id] = protein = self.get_or_create_protein(
                entrez_id=entrez_id,
                hgnc_symbol=hgnc_symbol,
                hgnc_id=hgnc_id,
            )
            self.session.add(protein)

        logger.info(f'Proteins: {len(entrez_id_protein)}')
        logger.info(f"Proteins w/o HGNC mapping: {len(missing_entrez_ids)}")

        for (
            wikipathways_id, _version, revision,
            pathway_name, species_name, entrez_ids,
        ) in tqdm(pathways, desc=f'v{version} serializing pathways'):
            proteins = [
                entrez_id_protein[entrez_id]
                for entrez_id in entrez_ids
            ]

            pathway = self.get_or_create_pathway(
                identifier=wikipathways_id,
                name=pathway_name.strip(),
                revision=revision,
                species=species_name_to_species[SPECIES_REMAPPING.get(species_name, species_name)],
                proteins=proteins,
            )
            self.session.add(pathway)

        self.session.commit()

    @classmethod
    def _cli_add_populate(cls, main: click.Group) -> click.Group:
        @main.command()
        @click.option('-r', '--reset', is_flag=True, help='Nuke database first')
        @click.option('-f', '--force', is_flag=True, help='Force overwrite if already populated')
        @click.option('-p', '--paths', multiple=True, help='URL of WikiPathways GMT files')
        @verbose_option
        @click.pass_obj
        def populate(manager: Manager, reset, force, paths):
            """Populate the database."""
            if reset:
                click.echo('Deleting the previous instance of the database')
                manager.drop_all()
                click.echo('Creating new models')
                manager.create_all()

            if manager.is_populated() and not force:
                click.echo('Database already populated. Use --force to overwrite')
                sys.exit(0)

            manager.populate(paths=paths)

        return main
