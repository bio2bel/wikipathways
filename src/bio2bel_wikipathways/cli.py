# -*- coding: utf-8 -*-

import click
import logging
import os
from pandas import DataFrame, Series

from bio2bel_wikipathways.constants import DEFAULT_CACHE_CONNECTION
from bio2bel_wikipathways.manager import Manager

log = logging.getLogger(__name__)

main = Manager.get_cli()


@main.command()
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
def export(connection):
    """Export all pathway - gene info to a excel file"""
    m = Manager(connection=connection)

    log.info("Querying the database")

    # https://stackoverflow.com/questions/19736080/creating-dataframe-from-a-dictionary-where-entries-have-different-lengths
    genesets = DataFrame(
        dict([
            (k, Series(list(v)))
            for k, v in m.export_genesets().items()
        ])
    )

    log.info("Geneset exported to '{}/wikipathways_gene_sets.xlsx'".format(os.getcwd()))

    genesets.to_excel('wikipathways_gene_sets.xlsx', index=False)


if __name__ == '__main__':
    main()
