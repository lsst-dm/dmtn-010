"""Comparison between GWCS and AST."""
# AST imports
from starlink import Ast
from starlink import Atl

# astropy imports
import gwcs
from gwcs import coordinate_frames as cf
from astropy.modeling import models
from astropy import units as u
from astropy import coordinates as coord

# generic imports
import numpy as np
import astropy.io.fits as pyfits

# had to muck with my pythonpath to get my own pyast fork in place.
import os
print os.environ['PYTHONPATH']


def build_gwcs(data):
    """Make a gWCS objects from data."""

    # get the basic WCS transformation from the FITS headers
    # Have to fake a keyword: https://github.com/spacetelescope/gwcs/issues/40
    data[1].header['WCSAXES'] = 2
    # fits_transform = gwcs.utils.make_fitswcs_transform(data[1].header)

    # to get all the parts of the FITS WCS transform, so we can insert
    # our distortion model in between.
    wcs_info = gwcs.utils.read_wcs_from_header(data[1].header)
    fits_linear = gwcs.utils.fitswcs_linear(wcs_info)
    projcode = gwcs.utils.get_projcode(wcs_info['CTYPE'])
    fits_tan = gwcs.utils.create_projection_transform(projcode).rename(projcode)
    # now get the rotation
    phip, lonp = [wcs_info['CRVAL'][i] for i in gwcs.utils.get_axes(wcs_info)[0]]
    thetap = 180
    n2c = models.RotateNative2Celestial(phip, lonp, thetap, name="crval")
    fits_tan_rot = fits_tan | n2c

    # Create a simple distortion model from two 2D polynomails
    x_distort = models.Polynomial2D(2, c1_0=1, c0_1=1)
    y_distort = models.Polynomial2D(2, c1_0=1, c0_1=1)
    distortion = models.Mapping((0, 1, 0, 1)) | x_distort & y_distort
    # A potentially useful test coordinate is the identity.
    distortion = models.Identity(2)

    print
    print fits_linear
    print fits_tan_rot
    print distortion
    print

    # Create some coordinate frames to map between
    detector = cf.Frame2D(name='detector', axes_order=(0, 1), unit=(u.pix, u.pix))
    focal = cf.Frame2D(name='focal', axes_order=(0, 1), unit=(u.pix, u.pix))
    tangent = cf.Frame2D(name='tangent', axes_order=(0, 1), unit=(u.arcmin, u.arcmin))
    sky = cf.CelestialFrame(name='icrs', reference_frame=coord.ICRS())

    # tuples of frame:mapping
    # The last frame has None for the transform.
    pipeline = [(detector, fits_linear),
                (focal, distortion),
                (tangent, fits_tan_rot),
                (sky, None)
                ]
    return gwcs.wcs.WCS(pipeline)


def build_ast(data):
    """Make some AST objects from the file."""
    data = pyfits.open(infile)
    frameset, encoding = Atl.readfitswcs(data[1], Iwc=True)

    # TBD: need to figure out how to construct a PolyMap.
    # TBD: this is from the pyast test.py file:
    # pm = Ast.PolyMap( [[1.2,1.,2.,0.],[-0.5,1.,1.,1.],[1.0,2.,0.,1.]])
    # UnitMap is the Identity map: input a coordinate and just output it.
    distortion = Ast.UnitMap(2)

    # The original mapping. simplify() it to get rid of loops, etc.
    map = frameset.getmapping(Ast.BASE, frameset.Nframe).simplify()
    newmap = Ast.CmpMap(map, distortion)

    # insert the new mapping
    pixframe = frameset.getframe(Ast.BASE)  # pointer to the base frame (pixel coords)
    newmap.invert()
    isky = frameset.Current
    frameset.addframe(frameset.Nframe, newmap, pixframe)
    newpix = frameset.Current
    frameset.Current = isky

    # Now delete the old frame. Why, I'm not sure.
    oldpix = frameset.Base
    frameset.Base = newpix
    frameset.removeframe(oldpix)

    return frameset


# Use some data from afwdata

# infile = '/Users/parejkoj/lsst/afwdata/CFHT/D4/cal-53535-i-797722_1.fits'
infile = '/Users/parejkoj/lsst/simastrom/validation_data_cfht/raw/849375p.fits.fz'
data = pyfits.open(infile)
data[1].data.shape
nx = data[1].shape[0]
ny = data[1].shape[1]


# GWCS

wcs = build_gwcs(data)
# print the on-sky coordinates of some pixels, and the corners
print wcs
print wcs(0, 0)
print wcs(100, 100)
print wcs.footprint(data[1].data.shape)


# AST

frameset = build_ast(data)
# print the on-sky coordinates of some pixels, and the corners
xpixel = [0, 100]
ypixel = [0, 100]
ra, dec = frameset.tran([xpixel, ypixel])
print (180/np.pi)*frameset.norm((ra[0], dec[0]))

# print frameset


# Now compare them!

# make a meshgrid of the pixel coordinates
xx = np.arange(0, nx)
yy = np.arange(0, ny)
xv, yv = np.meshgrid(xx, yy)
# How do these two match up in terms of processing time?
# %timeit timeit wcs(xv, yv)
# %timeit timeit frameset.tran((xv.flatten(), yv.flatten()))


result_gwcs = wcs(xv, yv)
result_ast = (180/np.pi)*frameset.tran((xv.flatten(), yv.flatten()))
# have to reshape the AST results, since they went in as flat arrays.
result_ast = (360+result_ast[0].reshape(ny, nx), result_ast[1].reshape(ny, nx))


# are the results basically the same?
print np.allclose(result_ast[0], result_gwcs[0])
print np.allclose(result_ast[1], result_gwcs[1])


frameset.trangrid([0, 2], [0, 2])
