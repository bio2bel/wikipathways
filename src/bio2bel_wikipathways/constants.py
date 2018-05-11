# -*- coding: utf-8 -*-

"""WikiPathways constants"""

import os

from bio2bel.utils import get_connection, get_data_dir

MODULE_NAME = 'wikipathways'
DATA_DIR = get_data_dir(MODULE_NAME)
DEFAULT_CACHE_CONNECTION = get_connection(MODULE_NAME)

CONFIG_FILE_PATH = os.path.join(DATA_DIR, 'config.ini')

HGNC = 'HGNC'
WIKIPATHWAYS = 'WIKIPATHWAYS'

# Human gene sets
HOMO_SAPIENS_GENE_SETS = 'http://data.wikipathways.org/20180510/gmt/wikipathways-20180510-gmt-Homo_sapiens.gmt'
