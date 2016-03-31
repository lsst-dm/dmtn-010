..
  Content of technical report.

  See http://docs.lsst.codes/en/latest/development/docs/rst_styleguide.html
  for a guide to reStructuredText writing.

  Do not put the title, authors or other metadata in this document;
  those are automatically added.

:tocdepth: 1

====================================================================
WCS/Distortion model requirements, options, and recommendations
====================================================================

LSST-DM currently uses WCSlib_ to persist/un-persist and manipulate
World Coordinate System (WCS) transformations. WCS-lib is based on the work by
Greisen & Calabretta, which is specifically focused on the FITS WCS standard.
This standard only supports distortion models involving 7th order polynomials, which severly limits its ability to describe complex focal plane and on-sky distortions.

.. _WCSlib: http://www.atnf.csiro.au/people/mcalabre/WCS/

Requirements
============

.. warning::
 This section currently under development!

Initial discussion of future WCS/distortion model requirements occurred in a
`Community posting <https://community.lsst.org/t/future-world-coordinate-system-requirements/521>`_.

 * shared serialization format with gWCS, to allow LSST files to be used in non-LSST code.
 * very complex, composed models.
 * Worst case: ~400 pixels at a time (postage stamps in multifit)

More TBD...

Options
=======

There are essentially 6 options available to us, with varying tradeoffs between
work required, flexibility, likely performance, callability from C++, and standardization in the broader community.

1. Develop our own
------------------

Following the grand tradition of past astronomy surveys, we could develop our
own WCS/distortion software (likely in C++, with a python interface),
independent of any existing implementation. This seems like an obviously bad
choice, given the work that has already gone into AST and gWCS.

Advantages
^^^^^^^^^^^

 * We have full control over the implementation of and interface to the models.

Disadvantages
^^^^^^^^^^^^^^

 * Significant time investment.
 * Yet Another WCS "Standard.""
 * WCS and distortion models are complex objects: usable interface is challenging
   to develop.
 * Lessons learned by previous groups would be hard to capture.

2. Build on top of WCS-lib
--------------------------

Instead of starting entirely from scratch, we could continue to build on top of
WCS-lib. This has the advantage that of not having to re-implement the FITS-WCS
standard, but may be limiting in what we would be able to build on top of it,
in addition to requiring nearly as much effort as option 1, above.

Advantages
^^^^^^^^^^^

 * We have nearly full control over the implementation of and interface to the models.
 * FITS-WCS standard immediately available to us.

Disadvantages
^^^^^^^^^^^^^^

 * Significant time investment.
 * Enhancements on top of FITS are Yet Another WCS "Standard."
 * FITS-WCS has inherent limitations in namespace, extensibility, flexibility.
 * WCS and distortion models are complex objects: usable interface is challenging
   to develop.
 * Lessons learned by previous groups would be hard to capture.

3. Adopt Starlink AST as-is
---------------------------

The `Starlink AST package <http://starlink.eao.hawaii.edu/starlink/AST>`_,
written in "Object Oriented C", provides a large suite of composeable
transformation classes, including mapping simplification to reduce the number of
steps required to e.g. go from one focal plane to another, possibly avoiding
having to transform all the way to the sky. It provides an option to compute a
transformation (sequence of mappings) using local linear approximations for fast
calculation. We could use AST directly in place of afw.wcs, exposing all of its
methods to the end user without a C++ interface.

Advantages
^^^^^^^^^^^

 * Minimal initial time investment.
 * FITS-WCS standard immediately available to us.
 * More complicated distortion models immediately available to us.
 * API for adding additional models.
 * AST is written in C, so is callable from C++.
 * Python interface to AST already developed: pyast.
 * Significant work already invested in performance, including a local linear approximation to a specified accuracy.
 * Signfiicant documentation already exists.

Disadvantages
^^^^^^^^^^^^^^
 
 * Existing documetation often opaque.
 * pyast documentation very sparse.
 * Written in "Object Oriented C" - major long-term maintainability question.
 * API could use significant refactoring.
 * David Berry will very likely retire around the time of LSST commissioning: LSST-DM would become the de-facto owners of AST.

4. Adopt Starlink AST with LSST C++ abstraction layer
-----------------------------------------------------

Instead of directly using AST, we could wrap it a C++ abstraction layer, making
the interface more similar to the current afw.wcs. This would require more
initial work than just using AST, and would require additional effort to write
an interface for any part of AST that we did not wrap that we discovered we
needed later.

Advantages
^^^^^^^^^^^

 * Allows flexibility in switching libraries in the future.
 * Abstract away some of the more confusing portions of C API.
 * FITS-WCS standard immediately available to us.
 * More complicated distortion models immediately available to us.
 * API for adding additional models.
 * AST is written in C, so is callable from C++.
 * Python interface to AST already developed: pyast.
 * Significant work already invested in performance.
 * Signfiicant documentation already exists.

Disadvantages
^^^^^^^^^^^^^^
 
 * Moderate time investment.
 * Cannot easily leverage full power of AST machinery.
 * Would have to provide separate documentation of our C++ API.
 * Existing documetation often opaque.
 * pyast documentation very sparse.
 * Written in "Object Oriented C" - major long-term maintainability question.
 * API could use significant refactoring.
 * David Berry will very likely retire around the time of LSST commissioning: LSST-DM would become the de-facto owners of AST.

5. Adopt AstroPy gWCS
---------------------

`GWCS <https://github.com/spacetelescope/gwcs>`_ is a Generalized World
Coordinate System library currently being developed by STScI for use by JWST. It
is written in pure python, and built on top of the
`astropy.modeling <http://docs.astropy.org/en/stable/modeling/>`_ framework.
Complex models can be built from more simple models via standard mathematical
operations, and can be composed and chained in serial and parallel. It is under
active development, so LSST could have a hand in shaping its future path.

Advantages
^^^^^^^^^^^

 * FITS-WCS standard immediately available to us (not clear if all portions of G&C 2002, C&G 2002, C. et al. 2004 are currently implemented).
 * More complicated distortion models immediately available to us.
 * Pure python, allowing easy extension.
 * API for adding additional models.
 * Signfiicant and understandable documentation already exists.
 * Community adoption likely very high.
 * Would share development effort with STScI.

Disadvantages
^^^^^^^^^^^^^^

 * Significant time investment: current code uses WCS in C++.
 * Not directly callable from C++: calls to python from C++ may incure signifcant overhead.
 * Model description framework is pure python: unclear if performance requirements can be met.
 * Ongoing development work: not all features we may need are available.
 * No effort yet on performance optimizations.

6. Work with David Berry to develop modern C++ version of AST
-------------------------------------------------------------

Section 6 of the `AST paper <http://arxiv.org/abs/1602.06681>`_ discusses
"lessons learned", including a statement that they would have developed it in
C++, if they were starting development now. David Berry is interested in
re-implementing AST in a modern language as a legacy to the community. LSST
could contract him out and guide the development of a new implentation of AST
that we could use from C++, while solving some of the current limitations in AST (e.g. adding quad-double precision for time, better unit support, unclear API).

Advantages
^^^^^^^^^^^

 * Lessons learned from AST development can be directly applied.
 * AST has significant test suite and would be a reference implementation to guide development.
 * LSST has influence on new API.
 * LSST can take long-term ownership of new system.
 * David Berry willing to be contracted out for development.
 * major portions of AST code likely can be copied to new interface with minimal changes (e.g. FITS WCS support).

Disadvantages
^^^^^^^^^^^^^^

 * Significant time investment (shared with David Berry).
 * Details of contract with East Asian Observatory need to be developed.
 * Requires LSST C++ expertise to design new API, and produce ideomatic C++.
 * Unclear how much LSST guidance would be required to make a long-term supportable, well documented API.

Recommendations
===============

.. warning::
 This section currently under development!

TBD
