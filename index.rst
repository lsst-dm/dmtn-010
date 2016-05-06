..
  Content of technical report.

  See http://docs.lsst.codes/en/latest/development/docs/rst_styleguide.html
  for a guide to reStructuredText writing.

  Do not put the title, authors or other metadata in this document;
  those are automatically added.

:tocdepth: 2

Introduction
============

LSST-DM currently uses WCSLIB_ to persist/un-persist and manipulate
World Coordinate System (WCS) transformations. WCSLIB is based on the work by
`Greisen & Calabretta 2002`_, which were incorporated into the `FITS WCS standard`_.
This standard only supports distortion models involving 7th order polynomials, which severly limits its ability to describe complex focal plane and on-sky distortions. Most previous projects have employed this, or a related FITS WCS-based library, usually with some home-built custom functionality, to manage their astrometric results.

.. _WCSLIB: http://www.atnf.csiro.au/people/mcalabre/WCS/
.. _Greisen & Calabretta 2002: http://adsabs.harvard.edu/abs/2002A%26A...395.1061G
.. _FITS WCS standard: http://fits.gsfc.nasa.gov/fits_wcs.html

There is no standardized method in the astronomical community to improve upon or extend the `FITS WCS standard`_. The `Simple Imaging Polynomial convention <http://fits.gsfc.nasa.gov/registry/sip.html>`_ allows a distortion model represented by a polynomial of up to 9th order. The DECam community pipeline uses the `TPV convention <http://fits.gsfc.nasa.gov/registry/tpvwcs.html>`_ which allows a 7th-order polynomial distortion correction. SDSS produced their own `asTran model <https://data.sdss.org/datamodel/files/PHOTO_REDUX/RERUN/RUN/astrom/asTrans.html>`_ to map the (row,column) coordinates from each field into `(mu,nu) <https://www.sdss3.org/dr8/algorithms/surveycoords.php>`_ great circle spherical coordinates via a 3rd order polynomial.

Two much more flexible, powerful, and extensible systems are Starlink AST_ and STScI's GWCS_. The Starlink AST_ package, developed by David Berry (East Asian Observatory) in C, with a python interface (PyAST_) written by Tim Jenness, provides models that can be combined in a variety of ways, but it is not widely used. Nadia Dencheva and Perry Greenfield (STScI) are developing a python-based Generalized World Coordinate System package (GWCS_), building top of `astropy.modeling`_ for JWST.

.. _AST: http://starlink.eao.hawaii.edu/starlink/AST
.. _PyAST: http://timj.github.io/starlink-pyast/pyast.html
.. _GWCS: https://github.com/spacetelescope/gwcs
.. _astropy.modeling: http://docs.astropy.org/en/stable/modeling/

This document discusses the expected requirements for the LSST distortion model and coordinate transform system, the options we have to select from, and provides a recommendation for how we should achieve our requirements.

Requirements
============

The initial call for discussion of future WCS/distortion model requirements was on this
`Community posting <https://community.lsst.org/t/future-world-coordinate-system-requirements/521>`_. Independently, Jim Bosch's `post about fitted models <https://community.lsst.org/t/interfaces-for-fitted-models/505>`_ presented some items which may guide our selection of transformation modeling systems.

LSST's most critical requirements are:

 * Specifying complex parametric and non-parametric models.
 * Arbitrary combinations/compositions of those models.
 * Ability to provide approximate WCSLIB_-style `FITS WCS standard`_ output, for legacy software use.
 * Fast pixel-to-pixel performance for warping, and on small (~400px) postage stamps in multifit.
 * Shared serialization format with GWCS_, to allow LSST files to be used in non-LSST code and vice-versa (at a recent joint meeting, LSST and AstroPy representatives discussed leveraging the work the IVOA has done on STC2_ as a possible route toward this). This requires that all transforms used by LSST are available within GWCS: LSST could contribute the required code to GWCS for any of our externally-visible transforms that they do not have.

.. _STC2: https://volute.g-vo.org/svn/trunk/projects/dm/vo-dml/models/STC2/2016-02-19/VO-DML-STC2.html
.. _AstroPy: http://www.astropy.org/

Coordinate and Transformation Requirements
------------------------------------------

 * The ability to model all pixel distortion effects that are frozen through one exposure (not Brighter-Fatter). These are likely our "exotic" ones--e.g. tree rings, edge roll-off--that are not yet included in any currently existing distortion modeling system.
 * Mappings between on-camera coordinate systems (i.e. the future versions of `afw.cameraGeom`_ and `afw.geom.XYTransform`_) must be entirely interoperable with image->sky (i.e. the future `afw.image.Wcs`_) transformations.

   * A method for easily creating simple WCS from e.g. existing files or a handful of on-sky values.
   * A method to easily produce an initial guess WCS by combining the post-ISR CCD geometry and telescope pointing, to feed into our astrometric solver.

 * Compositions of transforms should be simplifiable, for optimal performance and simpler serialization.

   * Compositions should only simplify when it can be done exactly (to machine precision), or when explicitly requested with a bound on accuracy.

 * Transforms should know their domain to ensure that composed transforms are valid between different domains.
 * Transforms should know whether they involve spherical-spherical, spherical-Cartesian, Cartesian-spherical, or Cartesian-Cartesian coordinates, to allow interoperability with geometry libraries that distinguish these coordinate systems.
 * Transforms should be invertible, or if not invertible should allow pre-defined one-way transforms to be identified as each-other's inverses.
 * Ability to efficiently obtain the exact transform at one point for warping. This needs to be fast and parallel.
 * Ability to efficiently obtain a local linear approximation around a point (must be parallel).
 * A method for obtaining a local TAN WCS approximation.
 * Transforms must be persistable as components of arbitrary objects (e.g. Exposure, Psf).

   * Groups of composed transforms should be persisted efficiently, e.g. for all CCDs in a visit, to reduce data size. It is unclear if this is actually necessary: the only obvious "heavyweight" transform is pixel distortion (e.g. tree rings), which is per-CCD anyway, while other transforms will likely be a very small part of our data volume.
   * An efficient (compressed?) persistence format for pixel-grid-based transformations will be necessary if we end up using full pixel grids to represent pixel distortions.

 * The ability to compute or provide derivatives with respect to pixel coordinates (to compute local affine transformations).

   * If we use the same system for Fitters as we do for Consumers (see :ref:`consumers-vs-fitters`), some transforms will need the ability to compute or provide (at least) first derivatives with respect to the parameters.

 * The ability to add more transforms in the future as we discover a need for them: polynomial/Chebyshev transforms are not enough.
 * We likely do `not` need to include wavelength-dependent effects (e.g. Differential Chromatic Refraction) in the WCS, if we define our PSFs with offset centroids.

.. _afw.cameraGeom: https://github.com/lsst/afw/tree/w.2016.15/python/lsst/afw/cameraGeom
.. _afw.image.Wcs: https://github.com/lsst/afw/blob/w.2016.15/include/lsst/afw/image/Wcs.h

.. _consumers-vs-fitters:

Models for Consumers vs. Fitters
--------------------------------

We may want to have separate model representations for astrometric fitting (Fitters) and for using the result of the fit (Consumers). In the current LSST stack, we have an afw.geom.XYTransform_ as the interface for the consumer (fitted) model, while the Gtransfo_ object introduced in jointcal is an interface for a particular fitter.

.. _afw.geom.XYTransform: https://github.com/lsst/afw/blob/w.2016.15/include/lsst/afw/geom/XYTransform.h
.. _Gtransfo: https://github.com/lsst/jointcal/blob/master/include/lsst/jointcal/Gtransfo.h

 * It is useful to separate the fitter from the consumer, as they may have different "best" internal representations.
 * It can be conceptually and programmatically helpful to have the same underlying system (or API) for both, to allow easy transfer between them.
 * Fitters `must` be mutable. Consumers need not be and may be better as immutable to allow the complex object to be safely shared across threads.
 * Consumers `must` be persistable. Fitters may not need to be.

As a related point, it could be useful to have the same model description system available for other purposes (e.g. representing galaxy shapes, `photometric calibration <http://arxiv.org/abs/1203.6255>`_).

Options
=======

There are essentially 6 options available to us, with varying trade-offs between work required, flexibility, likely performance, ease of calling from C++, and standardization in the broader community. These options are not necessarily mutually exclusive; in particular we could begin with :ref:`AST-as-is` or :ref:`AST-abstract` while developing a new system per :ref:`adoptGWCS` or :ref:`c++AST`. In addition, :ref:`AST-as-is` and :ref:`AST-abstract` are really two points in a continuum and we could evolve over time from one to the other as our needs and API design evolve.

.. _develop-own:

1. Develop our own
------------------

Following the grand tradition of past astronomy surveys, we could develop our
own WCS/distortion software (likely in C++, with a python interface),
independent of any existing implementation. This seems like an obviously bad
choice, given the work that has already gone into AST and GWCS.

.. _own-advantage:

Advantages
^^^^^^^^^^^

 * We have full control over the implementation of and interface to the models.

.. _own-disadvantage:

Disadvantages
^^^^^^^^^^^^^^

 * Significant time investment.
 * FITS WCS standard not immediately available to us.
 * Yet Another WCS "Standard".
 * WCS and distortion models are complex objects: usable interface is challenging
   to develop.
 * Lessons learned by previous groups would be hard to capture.

.. _use-wcslib:

2. Build on top of WCSLIB
--------------------------

Instead of starting entirely from scratch, we could continue to build on top of WCSLIB_. This has the advantage of not having to re-implement the `FITS WCS standard`_, but may be limiting in what we would be able to build on top of it, in addition to requiring nearly as much effort as option 1, above.

.. _wcslib-advantage:

Advantages
^^^^^^^^^^^

 * We have nearly full control over the implementation of and interface to the models.
 * FITS WCS standard immediately available to us.

.. _wcslib-disadvantage:

Disadvantages
^^^^^^^^^^^^^^

 * Significant time investment.
 * Enhancements on top of FITS are Yet Another WCS "Standard."
 * FITS WCS has inherent limitations in namespace, extensibility, flexibility.
 * WCS and distortion models are complex objects: usable interface is challenging
   to develop.
 * Lessons learned by previous groups would be hard to capture.

.. _AST-as-is:

3. Adopt Starlink AST as-is
---------------------------

The Starlink AST_ package, written in "Object Oriented C", provides a large suite of composable
transformation classes, including mapping simplification to reduce the number of
steps required to e.g. go from one focal plane to another, possibly avoiding
having to transform all the way to the sky. It provides an option to compute a
transformation (sequence of mappings) using local linear approximations for fast
calculation. We could use AST directly in place of afw.image.Wcs, exposing all of its
methods to the end user without a C++ interface.

.. _AST-as-is-advantage:

Advantages
^^^^^^^^^^^

 * Minimal initial time investment.
 * FITS WCS standard immediately available to us.
 * More complicated distortion models immediately available to us.
 * API for adding additional models.
 * AST is written in C, so is callable from C++.
 * Python interface to AST already developed: PyAST_.
 * Significant work already invested in performance, including a local linear approximation to a specified accuracy.
 * Significant documentation already exists.

.. _AST-as-is-disadvantage:

Disadvantages
^^^^^^^^^^^^^^

 * Existing documentation often opaque.
 * PyAST_ documentation very sparse.
 * Written in "Object Oriented C" - major long-term maintainability question.
 * API could use significant refactoring.
 * David Berry will very likely retire around the time of LSST commissioning: LSST-DM would become the de-facto owners of AST.

.. _AST-abstract:

4. Adopt Starlink AST with LSST C++ abstraction layer
-----------------------------------------------------

Instead of directly using AST_, we could wrap it a C++ abstraction layer, making
the interface more similar to the current afw.image.Wcs. This would require more
initial work than just using AST, and would require additional effort to write
an interface for any part of AST that we did not wrap that we discovered we
needed later.

.. _AST-abstract-advantage:

Advantages
^^^^^^^^^^^

 * Allows flexibility in switching libraries in the future.
 * Abstract away some of the more confusing portions of C API.
 * FITS WCS standard immediately available to us.
 * More complicated distortion models immediately available to us.
 * API for adding additional models.
 * AST is written in C, so is callable from C++.
 * Python interface to AST already developed: PyAST_.
 * Significant work already invested in performance.
 * Signfiicant documentation already exists.

.. _AST-abstract-disadvantage:

Disadvantages
^^^^^^^^^^^^^^

 * Moderate time investment.
 * Cannot easily leverage full power of AST machinery.
 * Would have to provide separate documentation of our C++ API.
 * Existing documentation often opaque.
 * PyAST_ documentation very sparse.
 * Written in "Object Oriented C" - major long-term maintainability question.
 * API could use significant refactoring.
 * David Berry will very likely retire around the time of LSST commissioning: LSST-DM would become the de-facto owners of AST.

.. _adoptGWCS:

5. Adopt AstroPy GWCS
---------------------

GWCS_ is a Generalized World Coordinate System library currently being developed by STScI for use by JWST. It is written in pure python, and built on top of the `astropy.modeling`_  framework.
Complex models can be built from more simple models via standard mathematical
operations, and can be composed and chained in serial and parallel. It is under
active development, so LSST could have a hand in shaping its future path.

.. _GWCS-advantage:

Advantages
^^^^^^^^^^^

 * FITS WCS standard immediately available to us (not clear if all portions of `Greisen & Calabretta 2002`_, `Calabretta & Greisen 2002`_, `Calabretta et al. 2004`_ are currently implemented).
 * More complicated distortion models immediately available to us.
 * Pure python, allowing easy extension.
 * Clean API for adding additional models.
 * Significant and understandable documentation already exists.
 * Community adoption likely very high.
 * Would share development effort with STScI.

.. _Greisen & Calabretta 2002: http://adsabs.harvard.edu/abs/2002A%26A...395.1061G
.. _Calabretta & Greisen 2002: http://adsabs.harvard.edu/abs/2002A%26A...395.1077C
.. _Calabretta et al. 2004: http://fits.gsfc.nasa.gov/wcs/dcs_20040422.pdf

.. _GWCS-disadvantage:

Disadvantages
^^^^^^^^^^^^^^

 * Significant time investment: current code manipulates WCS in C++.
 * Not directly callable from C++: calls to python from C++ may incur significant overhead.
 * Model description framework is pure python: unclear if performance requirements can be met, particularly for warping.
 * Ongoing development work: not all features we may need are available.
 * No effort yet on performance optimizations.

.. _c++AST:

6. Work with David Berry to develop modern C++ version of AST
-------------------------------------------------------------

Section 6 of the `AST paper <http://arxiv.org/abs/1602.06681>`_ discusses
"lessons learned", including a statement that they would have developed it in
C++, if they were starting development now. David Berry is interested in
re-implementing AST in a modern language as a legacy to the community. LSST
could contract him out and guide the development of a new implementation of AST
that we could use from C++, while solving some of the current limitations in AST (e.g. adding quad-double precision for time, better unit support, clearer API).

As part of this process, the `astropy.modeling`_ API should be used as a reference for how to create and combine models. Their method of using mathematical operations to combine transforms makes the creation of complicated models from simpler components highly intuitive, and presents a good design to build a C++ transformation system from.

.. _c++AST-advantage:

Advantages
^^^^^^^^^^^

 * Lessons learned from AST development can be directly applied.
 * AST has significant test suite and would be a reference implementation to guide development.
 * LSST has influence on new API.
 * LSST can take long-term ownership of new system.
 * David Berry willing to be contracted out for development.
 * major portions of AST code likely can be copied to new interface with minimal changes (e.g. FITS WCS support).

.. _c++AST-disadvantage:

Disadvantages
^^^^^^^^^^^^^^

 * Significant time investment (shared with David Berry).
 * Details of contract with East Asian Observatory need to be developed.
 * Requires LSST C++ expertise to design new API, and produce idiomatic C++.
 * Unclear how much LSST guidance would be required to make a long-term supportable, well documented API.

Recommendations
===============

Although adopting GWCS would be ideal from the perspective of community involvement, there are two main reasons we are not pursuing that option at this time:

 1. It is unclear whether GWCS would be able to achieve our required performance targets when computing transformations on small pixel regions. Our testing found a very `significant overhead`_ (10-20 times slower) when using GWCS over small (~100-1000) pixel regions (see the :doc:`performance test files here<_static/compare_gwcs_ast>`). Some of this overhead could be removed if LSST put effort into optimizing GWCS, but it is unclear whether optimizations to a python library would be sufficient for our needs. It is even less clear whether we could use a python-based WCS and transform library from within C++ without sustaining a significant performance penalty.
 2. Our current warping code--`afw.math.warpExposure`_--is written purely in C++ and would incur a significant effort to rewrite in python. Warping involves calculations on small patches in a manner that is not easily vectorized. Because of the concerns about performance on small patches described above, it is unclear if the new product would be performant enough to justify the effort.

So long as we insist on sharing a serialization format with GWCS and work together to ensure we can round-trip data between the projects, we would retain the option of using GWCS in the future.

Given the requirements, options, and caveats listed above, our recommendation is to immediately begin implementing a rewrite of `afw.image.Wcs`_, `afw.cameraGeom`_ and `afw.geom.XYTransform`_ on top of AST, while pursuing a new C++ rewrite of AST that takes into account the lessons learned from the design and API of astropy.modeling and GWCS. We will decide how much to abstract AST as we design the new afw API, and that API can help guide the new C++-based AST rewrite.

.. _significant overhead: https://jira.lsstcorp.org/browse/DM-5701
.. _afw.math.warpExposure: https://github.com/lsst/afw/blob/w.2016.15/include/lsst/afw/math/warpExposure.h
