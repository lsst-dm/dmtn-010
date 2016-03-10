# Notes about current WCS systems from reading documentation

## WCSLIB

The stack currently uses wcslib.

## FITS WCS I: Greisen & Calabretta 2002

http://www.aanda.org/articles/aa/full/2002/45/aah3859/aah3859.html

Generalizes FITS WCS keywords to "[describe] non-linear coordinate systems and any parameters that they may require"

"Hindsight also suggests that we were rather naive at the time concerning coordinates and it is fortunate that the detailed specification was postponed until greater experience could be obtained."

## FITS WCS II: Calabretta & Greisen 2002

http://www.aanda.org/articles/aa/full/2002/45/aah3860/aah3860.html

Generalization of the AIPS convention (Greisen 1983, 1986).

convention: fiducial coordinate (phi_0,theta_0) transforms to reference point (x,y) -> (0,0)

## FITS WCS IV: Calabretta et al. 2004

Describes distortions

## AST: Berry, Warren-Smith, Jenness 2015

Separate Frame (CS representation) from Mapping (computational transformation).

"One consequence of this is that users cannot easily create new sub-classes from AST objects without learning the internal conventions that it uses. At the time, this was seen as something of an advantage. ... However, with hind-sight a more open architecture may have encouraged involvement from a wider user-base."

"FITS header conventions (many of them informal) are in constant flux..."
"FITS header handling has proved one of the most complex areas to tame in AST..."

FrameSet: combination of various Frames and the mappings between them.

Mappings are immutable. Frames and FrameSets are mutable.

starlink-pyast: LGPL python interface to AST.

built-in simplification scheme.

"Integrity Restoration": if a Frame in a FrameSet is modified, the corresponding Mapping is modified to match. This can be circumvented.

Functions for plotting.

Can be applied to data values (not just their coordinate positions), e.g. FluxFrame.

astFindFrame: given a template (e.g. 2d sky coordinates), will return a mapping from some data (e.g. 2d galactic coords) to the template, if possible.

To resample/regrid data, AST tries to do a linear approximation in quadrants, reducing the size of said quadrants until the transformation matches a specified accuracy. Could this be a problem for us (needing very high accuracy), or is it always so much faster that it is worth while?

What would it take to re-implement in C++ per Section 6.1? Would it be worth it for us to make the interface match the internals? There's already a reference impelentation, so that would simplify things.

All coordinates are double-precision: do we need long doubles for anything?

Angles in radians: is there a way to handle that smoothly if we use astropy Units?
