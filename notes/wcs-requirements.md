# LSST coordinate requirements

https://community.lsst.org/t/future-world-coordinate-system-requirements/521/4

 * arbitrary composition of transformations.
 
 * pixel distortion effects that exist through one exposure (not B-F). These are likely our "exotic" ones.
 * mappings between coords on camera must be entirely interoperable with imagne->sky.
 * compositions should only simplify when it can be done exactly, or when explicitly requested with a bound on accuracy.
 * transforms should know their endpoints to ensure that composed transforms are valid to get between those endpoints.
 * distinguish between spherical and Cartesian, to ensure correct geometry.
 * likely do not need color/wavelength in WCS, if we define PSFs with offset centroids.
 * method to invert transforms. If not invertible, should allow pre-defined one-way transforms to be identified as each-other's inverses.
 * Efficiently obtain exact transform at one point for warping. Needs to be fast and parallel.
 * Efficient parallel local linear approximation at a point.
 * Persist as components of arbitrary objects.
 * Persist groups of composed transforms efficiently. Unclear if this is necessary: only obvious "heavyweight" transform is pixel distortion (e.g. tree rings), which is per-CCD.
 * Parameterizable to compute or provide (at least) first derivatives, to simplify connection wtih XYTransform etc.
 * Polynomial/Chebyshev transforms are not enough. Need ability to add transforms in the future.

 * single, efficient pixel-to-pixel transform for warping.
 * combined post-ISR CCD, including initial guess from pointing.
 * getTanWcs for comparisons and simple estimation.


XYTranform vs. Gtransfo
=======================

https://community.lsst.org/t/interfaces-for-fitted-models/505

XYTransform is interface for the consumer (fitted) model, Gtransfo is for fitters.

 * It's useful to separate fitter from consumer, as they may have different "best" representations.
 * It can be conceptually and programmatically helpful to have the same system (or API?) for both, to allow easy transfer between them.
 * fitters must be mutable. Consumer need not be, and may be better as immutable, allowing shared pointers, etc.
 * Consumer must be persistable, fitter may not.

# Useful papers/references

Relative photometric calibration: http://arxiv.org/abs/1203.6255
