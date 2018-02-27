Bio2BEL WikiPathways |build| |coverage| |docs|
==============================================
This package allows the enrichment of BEL networks with WikiPathways information by wrapping its RESTful API.
Furthermore, it is integrated in the `ComPath environment <https://github.com/ComPath>`_ for pathway database comparison.

Installation
------------
This code can be installed with :code:`pip3 install git+https://github.com/bio2bel/wikipathways.git`

Note that the `Bio2BEL HGNC <https://github.com/bio2bel/hgnc>`_ should be installed and loaded in order to map ENTREZ identifiers to HGNC Symbols and populate the database:
You can load Bio2BEL HGNC by running the following command in your terminal: :code:`python3 -m bio2bel_hgnc populate`

Functionalities and Commands
----------------------------
Following, the main functionalities and commands to work with this package:

- Populate local database with WikiPathways info :code:`python3 -m bio2bel_wikipathways populate`
- Run an admin site for simple querying and exploration :code:`python3 -m bio2bel_wikipathways web` (http://localhost:5000/admin/)
- Export gene sets for programmatic use :code:`python3 -m bio2bel_wikipathways export`

Citation
--------

- Slenter, D.N., et al WikiPathways: a multifaceted pathway database bridging metabolomics to other omics research Nucleic Acids Research, (2017)doi.org/10.1093/nar/gkx1064

- Kutmon, M., et al. WikiPathways: capturing the full diversity of pathway knowledge Nucl. Acids Res., 44, D488-D494 (2016) doi:10.1093/nar/gkv1024

- Kelder, T., et al. WikiPathways: building research communities on biological pathways. Nucleic Acids Res. 2012 Jan;40(Database issue):D1301-7


.. |build| image:: https://travis-ci.org/bio2bel/wikipathways.svg?branch=master
    :target: https://travis-ci.org/bio2bel/wikipathways
    :alt: Build Status

.. |coverage| image:: https://codecov.io/gh/bio2bel/wikipathways/coverage.svg?branch=master
    :target: https://codecov.io/gh/bio2bel/wikipathways?branch=master
    :alt: Coverage Status

.. |docs| image:: http://readthedocs.org/projects/bio2bel-wikipathways/badge/?version=latest
    :target: http://bio2bel.readthedocs.io/projects/wikipathways/en/latest/?badge=latest
    :alt: Documentation Status
