Bio2BEL WikiPathways |build| |coverage| |docs|
==============================================
This package converts WikiPathways to BEL. At the moment, the package parse, store, and export to a namespace all Homo sapiens pathways.
Furthermore, a small wrapper around the database allows to explore through a Flask-admin interface the database and perform simple queries.

Installation
------------
This code can be installed with :code:`pip3 install git+https://github.com/bio2bel/wikipathways.git`

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
