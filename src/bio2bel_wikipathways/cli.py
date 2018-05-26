# -*- coding: utf-8 -*-

import click
import logging
import os
from pandas import DataFrame, Series

from bio2bel_wikipathways.constants import DEFAULT_CACHE_CONNECTION
from bio2bel_wikipathways.manager import Manager

log = logging.getLogger(__name__)

main = Manager.get_cli()


if __name__ == '__main__':
    main()
