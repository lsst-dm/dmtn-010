"""Make a blank exposure with a simple WCS

This gives us a way to create a simple WCS in ast and gwcs without building
it piece by piece.
"""
from __future__ import division, print_function
import math

import numpy as np

import lsst.afw.geom as afwGeom
import lsst.afw.coord as afwCoord
import lsst.afw.image as afwImage
from lsst.daf.base import PropertySet

ExposurePath = "simple.fits"


def makeWcs(pixelScale, crPixPos, crValCoord, posAng=afwGeom.Angle(0.0), doFlipX=False, projection="TAN",
    radDecCSys="ICRS", equinox=2000):
    """Make a Wcs
    
    @param[in] pixelScale: desired scale, as sky/pixel, an afwGeom.Angle
    @param[in] crPixPos: crPix for WCS, using the LSST standard; a pair of floats
    @param[in] crValCoord: crVal for WCS (afwCoord.Coord)
    @param[in] posAng: position angle (afwGeom.Angle)
    @param[in] doFlipX: flip X axis?
    @param[in] projection: WCS projection (e.g. "TAN" or "STG")
    """
    if len(projection) != 3:
        raise RuntimeError("projection=%r; must have length 3" % (projection,))
    ctypeList = [("%-5s%3s" % (("RA", "DEC")[i], projection)).replace(" ", "-")
        for i in range(2)]
    ps = PropertySet()
    crPixFits = [ind + 1.0 for ind in crPixPos] # convert pix position to FITS standard
    crValDeg = crValCoord.getPosition(afwGeom.degrees)
    posAngRad = posAng.asRadians()
    pixelScaleDeg = pixelScale.asDegrees()
    print("pixelScale = %s deg = %s rad" % (pixelScale.asDegrees(), pixelScale.asRadians()))
    print("crPixPos = ", crPixPos)
    print("crVal = %s deg = %s rad" % (crValCoord.getPosition(afwGeom.degrees),
        crValCoord.getPosition(afwGeom.radians)))

    cdMat = np.array([[ math.cos(posAngRad), math.sin(posAngRad)],
                      [-math.sin(posAngRad), math.cos(posAngRad)]], dtype=float) * pixelScaleDeg
    if doFlipX:
        cdMat[:,0] = -cdMat[:,0]
    for i in range(2):
        ip1 = i + 1
        ps.add("CTYPE%1d" % (ip1,), ctypeList[i])
        ps.add("CRPIX%1d" % (ip1,), crPixFits[i])
        ps.add("CRVAL%1d" % (ip1,), crValDeg[i])
    ps.add("RADESYS", radDecCSys)
    ps.add("EQUINOX", equinox)
    ps.add("CD1_1", cdMat[0, 0])
    ps.add("CD2_1", cdMat[1, 0])
    ps.add("CD1_2", cdMat[0, 1])
    ps.add("CD2_2", cdMat[1, 1])
    return afwImage.makeWcs(ps)


def makeExposure():
    """Make a blank exposure with a simple TAN WCS
    """
    bbox = afwGeom.Box2I(afwGeom.Point2I(0,0), afwGeom.Extent2I(512, 512))
    crValCoord = afwCoord.IcrsCoord(45*afwGeom.degrees, 60*afwGeom.degrees)
    crPixPos = afwGeom.Box2D(bbox).getCenter()
    pixelScale = afwGeom.Angle(1.0e-5 * afwGeom.degrees)
    wcs = makeWcs(
        pixelScale=pixelScale,
        crPixPos=crPixPos,
        crValCoord=crValCoord,
    )
    return afwImage.ExposureF(bbox, wcs)

if __name__ == "__main__":
    exp = makeExposure()
    exp.writeFits(ExposurePath)
