# -*- coding: utf-8 -*-

"""Parser for Bio2BEL WikiPathways."""

from typing import List, Optional, Tuple

import requests
from requests_file import FileAdapter

from .constants import HOMO_SAPIENS_GENE_SETS


def _process_pathway_id(pathway_id):
    """Process the pathway id.

    :param str pathway_id: pathway id with suffix
    :rtype: str
    :return: processed pathway id
    """
    return pathway_id.split('_')[0]


def _get_pathway_name(line: str) -> str:
    """Split the pathway name word and returns the name.

    :param line: first word from gmt file
    :return: pathway name
    """
    return line.split('%')[0]


def _get_pathway_species(line):
    return line.split('%')[-1]


def _get_pathway_id(pathway_info_url):
    """Split the pathway info url and returns the id.

    :param pathway_info_url: first word from gmt file
    :rtype: str
    :return: pathway id
    """
    return pathway_info_url.replace('http://www.wikipathways.org/instance/', '')


GmtSummary = Tuple[str, str, str, List[str]]


def _process_line(line: str) -> GmtSummary:
    """Return the pathway name, species, url, and gene sets associated.

    :param line: gmt file line
    :return: pathway name
    :return: pathway species
    :return: pathway info url
    :return: genes set associated
    """
    name, identifier, *genes = [
        word.strip()
        for word in line.split('\t')
    ]

    return (
        _get_pathway_name(name),
        _get_pathway_species(name),
        _process_pathway_id(_get_pathway_id(identifier)),
        genes,
    )


def parse_gmt_file(url: Optional[str] = None) -> List[GmtSummary]:
    """Return file as list of pathway - gene sets (ENTREZ-identifiers).

    :param url: url from gmt file
    :return: line-based processed file
    """
    # Allow local file to be parsed
    session = requests.session()
    session.mount('file://', FileAdapter())

    # TODO parse out version information and send it forwards
    response = session.get(url or HOMO_SAPIENS_GENE_SETS)

    if response.status_code == 404:
        raise FileNotFoundError(
            'WikiPathways has updated their files, please visit this page "http://data.wikipathways.org/current/gmt/" '
            'and change the URL in constants.py')

    return [
        _process_line(line.decode('utf-8'))
        for line in response.iter_lines()
    ]
