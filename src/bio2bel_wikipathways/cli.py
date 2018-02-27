# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
import os

import click
from pandas import DataFrame, Series

from bio2bel_wikipathways.constants import DEFAULT_CACHE_CONNECTION
from bio2bel_wikipathways.manager import Manager
from bio2bel_wikipathways.to_belns import deploy_to_arty

log = logging.getLogger(__name__)


def set_debug(level):
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def set_debug_param(debug):
    if debug == 0:
        set_debug(30)
    elif debug == 1:
        set_debug(20)
    elif debug == 2:
        set_debug(10)


@click.group(help='Convert WikiPathways to BEL. Default connection at {}'.format(DEFAULT_CACHE_CONNECTION))
def main():
    logging.basicConfig(level=10, format="%(asctime)s - %(levelname)s - %(message)s")


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
@click.option('-d', '--reset-db', default=True)
def populate(debug, connection, reset_db):
    """Build the local version of WikiPathways."""
    set_debug_param(debug)

    m = Manager(connection=connection)

    if reset_db is True:
        log.info('Deleting the previous instance of the database')
        m.drop_all()
        log.info('Creating new models')
        m.create_all()

    click.echo("populate tables")
    m.populate(url=None)


@main.command()
@click.option('-v', '--debug', count=True, help="Turn on debugging.")
@click.option('-y', '--yes', is_flag=True)
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
def drop(debug, yes, connection):
    """Drop the WikiPathways database."""

    set_debug_param(debug)

    if yes or click.confirm('Do you really want to delete the database?'):
        m = Manager(connection=connection)
        click.echo("drop db")
        m.drop_all()


@main.command()
@click.option('--force', is_flag=True, help="Force knowledge to be uploaded even if not new namespace")
def deploy(force):
    """Deploy to Artifactory"""
    deploy_to_arty(not force)


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


@main.command()
@click.option('-c', '--connection', help="Defaults to {}".format(DEFAULT_CACHE_CONNECTION))
def web(connection):
    """Run web"""
    from bio2bel_wikipathways.web import create_app
    app = create_app(connection=connection)
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
