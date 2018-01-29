# -*- coding: utf-8 -*-

import requests

from .constants import HOMO_SAPIENS_GENE_SETS


def _get_pathway_name(line):
    """Split the pathway name word and returns the name

    :param line: first word from gmt file
    :rtype: str
    :return: pathway name
    """
    return line.split('%')[0]


def _get_pathway_id(pathway_info_url):
    """Split the pathway info url and returns the id

    :param pathway_info_url: first word from gmt file
    :rtype: str
    :return: pathway id
    """
    return pathway_info_url.replace('http://www.wikipathways.org/instance/', '')


def _process_line(line):
    """Returns pathway name, url and gene sets associated

    :param str line: gmt file line
    :rtype: str
    :return: pathway name
    :rtype: str
    :return: pathway info url
    :rtype: list[str]
    :return: genes set associated
    """
    processed_line = [
        word
        for word in line.split('\t')
    ]

    return _get_pathway_name(processed_line[0]), _get_pathway_id(processed_line[1]), processed_line[2:]


def parse_gmt_file(url=None):
    """Returns file as list of pathway - gene sets (ENTREZ-identifiers)

    :param Optional[str] url: url from gmt file
    :return: line-based processed file
    :rtype: list
    """

    response = requests.get(url or HOMO_SAPIENS_GENE_SETS)

    pathways = []

    for line in response.iter_lines():
        decoded_line = line.decode('utf-8')

        pathway_name, url_info, gene_set = _process_line(decoded_line)

        pathways.append((pathway_name, url_info, gene_set))

    return pathways
