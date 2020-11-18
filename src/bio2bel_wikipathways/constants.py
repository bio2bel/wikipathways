# -*- coding: utf-8 -*-

"""Constants for Bio2BEL WikiPathways."""

from dataclasses import dataclass
from typing import Dict

from bio2bel import get_data_dir
from bio2bel.utils import ensure_path

VERSION = '0.3.0-dev'

MODULE_NAME = 'wikipathways'
DATA_DIR = get_data_dir(MODULE_NAME)

HGNC = 'hgnc'
WIKIPATHWAYS = 'wikipathways'

DATA_VERSION = '20200310'


@dataclass
class SpeciesPathwayInfo:
    """Reference to a given taxon."""

    taxonomy_id: str
    name: str

    @property
    def url(self) -> str:  # noqa: D401
        """The URL for the data."""
        return f'http://data.wikipathways.org/{DATA_VERSION}/gmt/wikipathways-{DATA_VERSION}-gmt-{self.name}.gmt'

    @property
    def path(self) -> str:  # noqa: D401
        """The (ensured) path to the data."""
        return ensure_path(MODULE_NAME, self.url)


_PATHWAY_INFO = [
    ('Anopheles_gambiae', '7165'),
    ('Arabidopsis_thaliana', '3702'),
    ('Bos_taurus', '9913'),
    ('Caenorhabditis_elegans', '6239'),
    ('Canis_familiaris', '9615'),
    ('Danio_rerio', '7955'),
    ('Drosophila_melanogaster', '7227'),
    ('Equus_caballus', '9796'),
    ('Gallus_gallus', '9031'),
    ('Homo_sapiens', '9606'),
    ('Mus_musculus', '10090'),
    ('Oryza_sativa', '4530'),
    ('Pan_troglodytes', '9598'),
    ('Populus_trichocarpa', '3694'),
    ('Rattus_norvegicus', '10116'),
    ('Saccharomyces_cerevisiae', '4932'),
    ('Sus_scrofa', '9823'),

]

SPECIES_REMAPPING = {
    'Canis familiaris': 'Canis lupus familiaris',
}

infos: Dict[str, SpeciesPathwayInfo] = {
    taxonomy_id: SpeciesPathwayInfo(taxonomy_id=taxonomy_id, name=name)
    for name, taxonomy_id in _PATHWAY_INFO
}
