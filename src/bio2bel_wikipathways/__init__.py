# -*- coding: utf-8 -*-

"""A Bio2BEL package for WikiPathways.

Bio2BEL WikiPathways is a package for enriching BEL networks with WikiPathways information by wrapping its RESTful API.
WikiPathways is a pathway database containing multiple pathways for different species. This package downloads pathway
information from its API and store it in template data model relating genes to pathways. Furthermore, it is integrated
in the `ComPath environment <https://github.com/ComPath>`_ for pathway database comparison.

Citation
--------
- Slenter, D.N., et al WikiPathways: a multifaceted pathway database bridging metabolomics to other omics research
  Nucleic Acids Research, (2017)doi.org/10.1093/nar/gkx1064
- Kutmon, M., et al. WikiPathways: capturing the full diversity of pathway knowledge Nucl. Acids Res., 44, D488-D494
  (2016) doi:10.1093/nar/gkv1024
- Kelder, T., et al. WikiPathways: building research communities on biological pathways. Nucleic Acids Res. 2012
  Jan;40(Database issue):D1301-7
"""

from .manager import Manager  # noqa: F401
from .utils import get_version  # noqa: F401
