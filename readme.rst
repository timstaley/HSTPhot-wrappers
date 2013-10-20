HSTphot wrapper scripts - Readme
====================================

HSTphot_ is a remarkably effective software package for extracting sources from Hubble Space Telescope data. By using a semi-analytic model of the PSF across the detectors, extraction of faint sources can be achieved even in crowded fields. 

However, the package is composed of several smaller programs, which must be run in the right sequence with some slightly arcane command line arguments. To facilitate data reduction of archival HST data I put together these Python wrapper scripts.

Issues
========
Unfortunately, the code was written during my PhD, when I was:

1. still learning Python, and 
2. in a hurry. 

As a result the code is almost certainly poorly structured, minimally commented, and possibly buggy. Good luck!


.. _HSTphot: http://purcell.as.arizona.edu/hstphot/
