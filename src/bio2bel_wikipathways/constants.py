# -*- coding: utf-8 -*-

"""Constants for Bio2BEL WikiPathways."""

from bio2bel import get_data_dir

VERSION = '0.2.4-dev'

MODULE_NAME = 'wikipathways'
DATA_DIR = get_data_dir(MODULE_NAME)

HGNC = 'HGNC'
WIKIPATHWAYS = 'WIKIPATHWAYS'

#: Human gene sets
HOMO_SAPIENS_GENE_SETS = 'http://data.wikipathways.org/20190610/gmt/wikipathways-20190610-gmt-Homo_sapiens.gmt'
#: Fly gene sets
DROSOPHILA_GENE_SETS = 'http://data.wikipathways.org/20190610/gmt/wikipathways-20190610-gmt-Drosophila_melanogaster.gmt'
