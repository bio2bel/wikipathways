# -*- coding: utf-8 -*-

"""Constants for Bio2BEL WikiPathways."""

from bio2bel import get_data_dir

VERSION = '0.2.1'

MODULE_NAME = 'wikipathways'
DATA_DIR = get_data_dir(MODULE_NAME)

HGNC = 'HGNC'
WIKIPATHWAYS = 'WIKIPATHWAYS'

# Human gene sets
HOMO_SAPIENS_GENE_SETS = 'http://data.wikipathways.org/20180510/gmt/wikipathways-20180510-gmt-Homo_sapiens.gmt'
