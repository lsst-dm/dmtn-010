#!/usr/bin/env ipython
"""Comparison between GWCS and AST.

You must run this with ipython and you must create simple.fits first. Thus:
$ python makeExposure.py
$ ipython compare_gwcs_ast.py
"""
import os.path

import numpy as np
import astropy.io.fits as pyfits

# PyAST imports
from starlink import Ast, Atl

# astropy imports
import gwcs
from gwcs import coordinate_frames as cf
from astropy.modeling import models
from astropy import units as u
from astropy import coordinates as coord


def get_pix_to_meanpix_coeffs():
    """Return Polynomial2D coefficients for the pix to meanpix map

    Return a tuple of three items:
    - polynomial order
    - x coeff
    - y coeff
    the coefficients are for powers: x0y0, x0y1, x1y0, x0y2, x1y1, x2y2, ...
    """
    return [
        3,
        [
            0,
            1.0001, 1e-4,
            1e-6, 1e-6, 1e-6,
        ],
        [
            0,
            1e-4, 1.0002,
            1e-6, 1e-6, 1e-6,
        ],
    ]


def ast_poly_coeff_iter(ind, coeffs):
    """An iterator for ast poly coeffs for the given index: x=1, y=2

    @param[in] ind: output index: 0 for x, 1 for y
    @param[in] coeffs: list of coefficients for that index, as returned by get_pix_to_meanpix_coeffs

    @return a tuple containing the following (all cast to float):
    - coeff
    - ind (the input argument)
    - x power
    - y power
    """
    xpower = 0
    ypower = 0
    for coeff in coeffs:
        if coeff != 0:
            yield (coeff, float(ind+1), float(xpower), float(ypower))
        if ypower == 0:
            ypower = xpower + 1
            xpower = 0
        else:
            ypower -= 1
            xpower += 1


def make_ast_actpix_to_meanpix(acc=1e-3, maxacc=1e-4, maxorder=3, minxy=(0, 0), maxxy=(512, 512)):
    """Make an Ast.PolyMap model for actual pixels to pixels

    The forward transform is specified by coefficients from get_pix_to_meanpix_coeffs, whereas
    the reverse transform is fit. The arguments control the reverse transform fit.

    @param[in] acc  desired accuracy of reverse transform fit
    @param[in] maxacc  maximum accuracy of reverse transform fit
    @param[in] maxorder  maximum order of reverse transform fit
    @param[in] minxy  minimum x,y over which reverse transform will be fit
    @param[in] maxxy  maximum x,y over which reverse transform will be fit
    """
    # create forward transformation
    order, xcoeffs, ycoeffs = get_pix_to_meanpix_coeffs()
    xastcoeffs = tuple(ast_poly_coeff_iter(0, xcoeffs))
    yastcoeffs = tuple(ast_poly_coeff_iter(1, ycoeffs))
    polymap = Ast.PolyMap(xastcoeffs + yastcoeffs)
    #
    # fit reverse transformation; 2nd argument is 0 to fit reverse
    polymap = polymap.polytran(0, acc, maxacc, maxorder, minxy, maxxy)
    if polymap is None:
        raise RuntimeError("Could not compute inverse Ast.PolyMap")
    return polymap


def make_astropy_poly2d(order, coeffs):
    """Make an astropy models.Polynomial2D

    @param[in] order  order of pollynomial
    @param[in] coeffs  list of coefficients for one output axis;
        one of the two arrays returned by get_pix_to_meanpix_coeffs
    """
    coeffdict = dict()
    xpower = 0
    ypower = 0
    for coeff in coeffs:
        if coeff != 0:
            coeffname = "c%d_%d" % (xpower, ypower)
            coeffdict[coeffname] = coeff
        if ypower == 0:
            ypower = xpower + 1
            xpower = 0
        else:
            ypower -= 1
            xpower += 1
    return models.Polynomial2D(order, **coeffdict)


def make_astropy_actpix_to_meanpix():
    """Make an astropy.model model for actual pixels to mean pixels

    Uses the coefficients returned by get_pix_to_meanpix_coeffs
    """
    order, xcoeffs, ycoeffs = get_pix_to_meanpix_coeffs()
    xmodel, ymodel = [make_astropy_poly2d(order, coeffs) for coeffs in (xcoeffs, ycoeffs)]
    return models.Mapping((0, 1, 0, 1)) | xmodel & ymodel


def build_gwcs(hdu):
    """Make a gWCS objects from a pyfits HDU of an image, which should contain a simple TAN WCS
    """
    # to get all the parts of the FITS WCS transform, so we can insert
    # our distortion model in between.
    hdu.header["WCSAXES"] = 2
    wcs_info = gwcs.utils.read_wcs_from_header(hdu.header)
    fits_linear = gwcs.utils.fitswcs_linear(wcs_info)
    projcode = gwcs.utils.get_projcode(wcs_info['CTYPE'])
    fits_tan = gwcs.utils.create_projection_transform(projcode).rename(projcode)
    # now get the rotation
    phip, lonp = [wcs_info['CRVAL'][i] for i in gwcs.utils.get_axes(wcs_info)[0]]
    thetap = 180
    n2c = models.RotateNative2Celestial(phip, lonp, thetap, name="crval")
    fits_tan_rot = fits_tan | n2c

    actpix_to_pix = make_astropy_actpix_to_meanpix()

    # Create some coordinate frames to map between
    actpix = cf.Frame2D(name='actual_pixels', axes_order=(0, 1), unit=(u.pix, u.pix))
    pix = cf.Frame2D(name='pixels', axes_order=(0, 1), unit=(u.pix, u.pix))
    focal = cf.Frame2D(name='focal', axes_order=(0, 1), unit=(u.pix, u.pix))
    sky = cf.CelestialFrame(name='icrs', reference_frame=coord.ICRS())

    # tuples of frame:mapping
    # The last frame has None for the transform.
    pipeline = [(actpix, actpix_to_pix),
                (pix, fits_linear),
                (focal, fits_tan_rot),
                (sky, None)
                ]
    return gwcs.wcs.WCS(pipeline)


def build_ast(hdu):
    """Make an AST-based WCS from a pyfits HDU of an image, which should contain a simple TAN WCS
    """
    fitschan = Ast.FitsChan(Atl.PyFITSAdapter(hdu))
    # Set Iwc to True to leave a place to insert optical distortion;
    # it seems harmless and doesn't affect timing, but does make the frameset more complicated
    fitschan.Iwc = True
    frameset = fitschan.read()
    pix_frame_ind = frameset.Base
    sky_frame_ind = frameset.Current
    # print "TAN WCS frameset:\n", frameset

    # map of actual pixel to nominal pixel represented by a 2-d polynomial
    actpix_to_pix_map = make_ast_actpix_to_meanpix(maxxy=hdu.data.shape)
    actpix_frame = Ast.Frame(2, "Domain=GRID")

    # add this to the frameset
    # temporarily set inverse=true because it is inserted as a mapping from mean pixels to pixels
    # inserting sets current to the new frameset, so record that index
    actpix_to_pix_map.Invert = 1
    try:
        frameset.addframe(pix_frame_ind, actpix_to_pix_map, actpix_frame)
    finally:
        actpix_to_pix_map.Invert = 0
    actpix_frame_ind = frameset.Current

    # set meanpix as the base and sky as the current
    frameset.Base = actpix_frame_ind
    frameset.Current = sky_frame_ind

    return frameset


if __name__ == "__main__":
    currdir = os.path.dirname(__file__)
    infile = os.path.join(currdir, "simple.fits.gz")
    hdu = pyfits.open(infile)[1] # reading in a MaskedImage; image is in HDU 1
    imarr = hdu.data

    gwcs_wcs = build_gwcs(hdu)

    ast_wcs = build_ast(hdu)

    print "*** Verifying that GWCS and AST give the same results"

    nx = imarr.shape[0]
    ny = imarr.shape[1]
    xx = np.arange(0, nx)
    yy = np.arange(0, ny)
    xv, yv = np.meshgrid(xx, yy)
    result_gwcs = gwcs_wcs(xv, yv)
    result_ast = (180/np.pi)*ast_wcs.tran((xv.flatten(), yv.flatten()))
    result_ast = (result_ast[0].reshape(ny, nx), result_ast[1].reshape(ny, nx))
    result_trangrid = (180/np.pi) * ast_wcs.trangrid([0, 0], [511, 511])
    result_trangrid = (result_trangrid[0].reshape(ny, nx), result_trangrid[1].reshape(ny, nx))

    assert np.allclose(result_ast[0], result_gwcs[0])
    assert np.allclose(result_ast[1], result_gwcs[1])
    assert np.allclose(result_ast[1], result_trangrid[1])

    # What does the tolerence parameter actually mean? Once we know this may be a useful test:
    # print "How divergent is trangrid if we specify a tolerance?"
    # result_trangrid = (180/np.pi) * ast_wcs.trangrid([0, 0], [511, 511], 1000)
    # result_trangrid = (result_trangrid[0].reshape(ny, nx), result_trangrid[1].reshape(ny, nx))
    # print np.allclose(result_ast[1], result_trangrid[1])

    print "*** Passed!"


    # Timing comparisons

    magic = get_ipython().magic  # flake8: noqa: ipython-specific code

    nx = imarr.shape[0]
    ny = imarr.shape[1]
    for numxpts in (10, 100, 1000):
        numypts = numxpts
        xx = np.linspace(0, nx, numxpts)
        yy = np.linspace(0, ny, numypts)
        xv, yv = np.meshgrid(xx, yy)
        numpts = numxpts*numypts

        print("\n*** Timing pixel->sky for %d points" % (numpts,))

        print("gwcs:")
        magic('%timeit gwcs_wcs(xv, yv)')
        print("ast trans:")
        magic('%timeit ast_wcs.tran((xv.flatten(), yv.flatten()))')
        print("ast trangrid with tol=1e-3:")
        magic('%timeit ast_wcs.trangrid([0, 0], [511, 511], 1e-3)')
