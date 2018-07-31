Bio2BEL WikiPathways |build| |coverage| |documentation| |zenodo|
================================================================
This package allows the enrichment of BEL networks with WikiPathways information by wrapping its RESTful API.
Furthermore, it is integrated in the `ComPath environment <https://github.com/ComPath>`_ for pathway database
comparison.

Installation |pypi_version| |python_versions| |pypi_license|
------------------------------------------------------------
``bio2bel_wikipathways`` can be installed easily from `PyPI <https://pypi.python.org/pypi/bio2bel_wikipathways>`_ with
the following code in your favorite terminal:

.. code-block:: sh

    $ python3 -m pip install bio2bel_wikipathways

or from the latest code on `GitHub <https://github.com/bio2bel/wikipathways>`_ with:

.. code-block:: sh

    $ python3 -m pip install git+https://github.com/bio2bel/wikipathways.git@master

Setup
-----
WikiPathways can be downloaded and populated from either the Python REPL or the automatically installed command line
utility.

The following resources will be automatically installed and loaded in order to fully populate the tables of the
database:

- `Bio2BEL HGNC <https://github.com/bio2bel/hgnc>`_

Python REPL
~~~~~~~~~~~
.. code-block:: python

    >>> import bio2bel_wikipathways
    >>> wikipathways_manager = bio2bel_wikipathways.Manager()
    >>> wikipathways_manager.populate()

Command Line Utility
~~~~~~~~~~~~~~~~~~~~
.. code-block:: bash

    bio2bel_wikipathways populate

Other Command Line Utilities
----------------------------
- Run an admin site for simple querying and exploration :code:`python3 -m bio2bel_wikipathways web` (http://localhost:5000/admin/)
- Export gene sets for programmatic use :code:`python3 -m bio2bel_wikipathways export`

Citation
--------
- Slenter, D.N., et al WikiPathways: a multifaceted pathway database bridging metabolomics to other omics research
  Nucleic Acids Research, (2017) doi.org/10.1093/nar/gkx1064
- Kutmon, M., et al. WikiPathways: capturing the full diversity of pathway knowledge Nucl. Acids Res., 44, D488-D494
  (2016) doi:10.1093/nar/gkv1024
- Kelder, T., et al. WikiPathways: building research communities on biological pathways. Nucleic Acids Res. 2012
  Jan;40(Database issue):D1301-7

.. |build| image:: https://travis-ci.org/bio2bel/wikipathways.svg?branch=master
    :target: https://travis-ci.org/bio2bel/wikipathways
    :alt: Build Status

.. |coverage| image:: https://codecov.io/gh/bio2bel/wikipathways/coverage.svg?branch=master
    :target: https://codecov.io/gh/bio2bel/wikipathways?branch=master
    :alt: Coverage Status

.. |documentation| image:: http://readthedocs.org/projects/bio2bel-interpro/badge/?version=latest
    :target: http://bio2bel.readthedocs.io/projects/wikipathways/en/latest/?badge=latest
    :alt: Documentation Status

.. |climate| image:: https://codeclimate.com/github/bio2bel/wikipathways/badges/gpa.svg
    :target: https://codeclimate.com/github/bio2bel/wikipathways
    :alt: Code Climate

.. |python_versions| image:: https://img.shields.io/pypi/pyversions/bio2bel_wikipathways.svg
    :alt: Stable Supported Python Versions

.. |pypi_version| image:: https://img.shields.io/pypi/v/bio2bel_wikipathways.svg
    :alt: Current version on PyPI

.. |pypi_license| image:: https://img.shields.io/pypi/l/bio2bel_wikipathways.svg
    :alt: MIT License

.. |zenodo| image:: https://zenodo.org/badge/118924155.svg
    :target: https://zenodo.org/badge/latestdoi/118924155
