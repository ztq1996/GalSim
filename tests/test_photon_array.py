# Copyright (c) 2012-2021 by the GalSim developers team on GitHub
# https://github.com/GalSim-developers
#
# This file is part of GalSim: The modular galaxy image simulation toolkit.
# https://github.com/GalSim-developers/GalSim
#
# GalSim is free software: redistribution and use in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions, and the disclaimer given in the accompanying LICENSE
#    file.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions, and the disclaimer given in the documentation
#    and/or other materials provided with the distribution.
#

from __future__ import print_function
import unittest
import numpy as np
import os
import sys
import warnings

try:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        import astroplan
    no_astroplan = False
except ImportError:
    no_astroplan = True

import galsim
from galsim_test_helpers import *

bppath = os.path.join(galsim.meta_data.share_dir, "bandpasses")
sedpath = os.path.join(galsim.meta_data.share_dir, "SEDs")


@timer
def test_photon_array():
    """Test the basic methods of PhotonArray class
    """
    nphotons = 1000

    # First create from scratch
    photon_array = galsim.PhotonArray(nphotons)
    assert len(photon_array.x) == nphotons
    assert len(photon_array.y) == nphotons
    assert len(photon_array.flux) == nphotons
    assert not photon_array.hasAllocatedWavelengths()
    assert not photon_array.hasAllocatedAngles()

    # Initial values should all be 0
    np.testing.assert_array_equal(photon_array.x, 0.)
    np.testing.assert_array_equal(photon_array.y, 0.)
    np.testing.assert_array_equal(photon_array.flux, 0.)

    # Check picklability
    do_pickle(photon_array)

    # Check assignment via numpy [:]
    photon_array.x[:] = 5
    photon_array.y[:] = 17
    photon_array.flux[:] = 23
    np.testing.assert_array_equal(photon_array.x, 5.)
    np.testing.assert_array_equal(photon_array.y, 17.)
    np.testing.assert_array_equal(photon_array.flux, 23.)

    # Check assignment directly to the attributes
    photon_array.x = 25
    photon_array.y = 37
    photon_array.flux = 53
    np.testing.assert_array_equal(photon_array.x, 25.)
    np.testing.assert_array_equal(photon_array.y, 37.)
    np.testing.assert_array_equal(photon_array.flux, 53.)

    # Now create from shooting a profile
    obj = galsim.Exponential(flux=1.7, scale_radius=2.3)
    rng = galsim.UniformDeviate(1234)
    photon_array = obj.shoot(nphotons, rng)
    orig_x = photon_array.x.copy()
    orig_y = photon_array.y.copy()
    orig_flux = photon_array.flux.copy()
    assert len(photon_array.x) == nphotons
    assert len(photon_array.y) == nphotons
    assert len(photon_array.flux) == nphotons
    assert not photon_array.hasAllocatedWavelengths()
    assert not photon_array.hasAllocatedAngles()

    # Check arithmetic ops
    photon_array.x *= 5
    photon_array.y += 17
    photon_array.flux /= 23
    np.testing.assert_almost_equal(photon_array.x, orig_x * 5.)
    np.testing.assert_almost_equal(photon_array.y, orig_y + 17.)
    np.testing.assert_almost_equal(photon_array.flux, orig_flux / 23.)

    # Check picklability again with non-zero values
    do_pickle(photon_array)

    # Now assign to the optional arrays
    photon_array.dxdz = 0.17
    assert photon_array.hasAllocatedAngles()
    assert not photon_array.hasAllocatedWavelengths()
    np.testing.assert_array_equal(photon_array.dxdz, 0.17)
    np.testing.assert_array_equal(photon_array.dydz, 0.)

    photon_array.dydz = 0.59
    np.testing.assert_array_equal(photon_array.dxdz, 0.17)
    np.testing.assert_array_equal(photon_array.dydz, 0.59)

    # Check shooting negative flux
    obj = galsim.Exponential(flux=-1.7, scale_radius=2.3)
    rng = galsim.UniformDeviate(1234)
    neg_photon_array = obj.shoot(nphotons, rng)
    np.testing.assert_array_equal(neg_photon_array.x, orig_x)
    np.testing.assert_array_equal(neg_photon_array.y, orig_y)
    np.testing.assert_array_equal(neg_photon_array.flux, -orig_flux)

    # Start over to check that assigning to wavelength leaves dxdz, dydz alone.
    photon_array = obj.shoot(nphotons, rng)
    photon_array.wavelength = 500.
    assert photon_array.hasAllocatedWavelengths()
    assert not photon_array.hasAllocatedAngles()
    np.testing.assert_array_equal(photon_array.wavelength, 500)

    photon_array.dxdz = 0.23
    photon_array.dydz = 0.88
    photon_array.wavelength = 912.
    assert photon_array.hasAllocatedWavelengths()
    assert photon_array.hasAllocatedAngles()
    np.testing.assert_array_equal(photon_array.dxdz, 0.23)
    np.testing.assert_array_equal(photon_array.dydz, 0.88)
    np.testing.assert_array_equal(photon_array.wavelength, 912)

    # Check toggling is_corr
    assert not photon_array.isCorrelated()
    photon_array.setCorrelated()
    assert photon_array.isCorrelated()
    photon_array.setCorrelated(False)
    assert not photon_array.isCorrelated()
    photon_array.setCorrelated(True)
    assert photon_array.isCorrelated()

    # Check rescaling the total flux
    flux = photon_array.flux.sum()
    np.testing.assert_almost_equal(photon_array.getTotalFlux(), flux)
    photon_array.scaleFlux(17)
    np.testing.assert_almost_equal(photon_array.getTotalFlux(), 17*flux)
    photon_array.setTotalFlux(199)
    np.testing.assert_almost_equal(photon_array.getTotalFlux(), 199)
    photon_array.scaleFlux(-1.7)
    np.testing.assert_almost_equal(photon_array.getTotalFlux(), -1.7*199)
    photon_array.setTotalFlux(-199)
    np.testing.assert_almost_equal(photon_array.getTotalFlux(), -199)

    # Check rescaling the positions
    x = photon_array.x.copy()
    y = photon_array.y.copy()
    photon_array.scaleXY(1.9)
    np.testing.assert_almost_equal(photon_array.x, 1.9*x)
    np.testing.assert_almost_equal(photon_array.y, 1.9*y)

    # Check ways to assign to photons
    pa1 = galsim.PhotonArray(50)
    pa1.x = photon_array.x[:50]
    for i in range(50):
        pa1.y[i] = photon_array.y[i]
    pa1.flux[0:50] = photon_array.flux[:50]
    pa1.dxdz = photon_array.dxdz[:50]
    pa1.dydz = photon_array.dydz[:50]
    pa1.wavelength = photon_array.wavelength[:50]
    np.testing.assert_almost_equal(pa1.x, photon_array.x[:50])
    np.testing.assert_almost_equal(pa1.y, photon_array.y[:50])
    np.testing.assert_almost_equal(pa1.flux, photon_array.flux[:50])
    np.testing.assert_almost_equal(pa1.dxdz, photon_array.dxdz[:50])
    np.testing.assert_almost_equal(pa1.dydz, photon_array.dydz[:50])
    np.testing.assert_almost_equal(pa1.wavelength, photon_array.wavelength[:50])

    # Check assignAt
    pa2 = galsim.PhotonArray(100)
    pa2.assignAt(0, pa1)
    pa2.assignAt(50, pa1)
    np.testing.assert_almost_equal(pa2.x[:50], pa1.x)
    np.testing.assert_almost_equal(pa2.y[:50], pa1.y)
    np.testing.assert_almost_equal(pa2.flux[:50], pa1.flux)
    np.testing.assert_almost_equal(pa2.dxdz[:50], pa1.dxdz)
    np.testing.assert_almost_equal(pa2.dydz[:50], pa1.dydz)
    np.testing.assert_almost_equal(pa2.wavelength[:50], pa1.wavelength)
    np.testing.assert_almost_equal(pa2.x[50:], pa1.x)
    np.testing.assert_almost_equal(pa2.y[50:], pa1.y)
    np.testing.assert_almost_equal(pa2.flux[50:], pa1.flux)
    np.testing.assert_almost_equal(pa2.dxdz[50:], pa1.dxdz)
    np.testing.assert_almost_equal(pa2.dydz[50:], pa1.dydz)
    np.testing.assert_almost_equal(pa2.wavelength[50:], pa1.wavelength)

    # Error if it doesn't fit.
    assert_raises(ValueError, pa2.assignAt, 90, pa1)

    # Test some trivial usage of makeFromImage
    zero = galsim.Image(4,4,init_value=0)
    photons = galsim.PhotonArray.makeFromImage(zero)
    print('photons = ',photons)
    assert len(photons) == 16
    np.testing.assert_array_equal(photons.flux, 0.)

    ones = galsim.Image(4,4,init_value=1)
    photons = galsim.PhotonArray.makeFromImage(ones)
    print('photons = ',photons)
    assert len(photons) == 16
    np.testing.assert_almost_equal(photons.flux, 1.)

    tens = galsim.Image(4,4,init_value=8)
    photons = galsim.PhotonArray.makeFromImage(tens, max_flux=5.)
    print('photons = ',photons)
    assert len(photons) == 32
    np.testing.assert_almost_equal(photons.flux, 4.)

    assert_raises(ValueError, galsim.PhotonArray.makeFromImage, zero, max_flux=0.)
    assert_raises(ValueError, galsim.PhotonArray.makeFromImage, zero, max_flux=-2)

    # Check some other errors
    undef = galsim.Image()
    assert_raises(galsim.GalSimUndefinedBoundsError, pa2.addTo, undef)

    # Check picklability again with non-zero values for everything
    do_pickle(photon_array)

@timer
def test_convolve():
    nphotons = 1000000

    obj = galsim.Gaussian(flux=1.7, sigma=2.3)
    rng = galsim.UniformDeviate(1234)
    pa1 = obj.shoot(nphotons, rng)
    rng2 = rng.duplicate()  # Save this state.
    pa2 = obj.shoot(nphotons, rng)

    # If not correlated then convolve is deterministic
    conv_x = pa1.x + pa2.x
    conv_y = pa1.y + pa2.y
    conv_flux = pa1.flux * pa2.flux * nphotons

    np.testing.assert_allclose(np.sum(pa1.flux), 1.7)
    np.testing.assert_allclose(np.sum(pa2.flux), 1.7)
    np.testing.assert_allclose(np.sum(conv_flux), 1.7*1.7)

    np.testing.assert_allclose(np.sum(pa1.x**2)/nphotons, 2.3**2, rtol=0.01)
    np.testing.assert_allclose(np.sum(pa2.x**2)/nphotons, 2.3**2, rtol=0.01)
    np.testing.assert_allclose(np.sum(conv_x**2)/nphotons, 2.*2.3**2, rtol=0.01)

    np.testing.assert_allclose(np.sum(pa1.y**2)/nphotons, 2.3**2, rtol=0.01)
    np.testing.assert_allclose(np.sum(pa2.y**2)/nphotons, 2.3**2, rtol=0.01)
    np.testing.assert_allclose(np.sum(conv_y**2)/nphotons, 2.*2.3**2, rtol=0.01)

    pa3 = galsim.PhotonArray(nphotons)
    pa3.assignAt(0, pa1)  # copy from pa1
    pa3.convolve(pa2)
    np.testing.assert_allclose(pa3.x, conv_x)
    np.testing.assert_allclose(pa3.y, conv_y)
    np.testing.assert_allclose(pa3.flux, conv_flux)

    # If one of them is correlated, it is still deterministic.
    pa3.assignAt(0, pa1)
    pa3.setCorrelated()
    pa3.convolve(pa2)
    np.testing.assert_allclose(pa3.x, conv_x)
    np.testing.assert_allclose(pa3.y, conv_y)
    np.testing.assert_allclose(pa3.flux, conv_flux)

    pa3.assignAt(0, pa1)
    pa3.setCorrelated(False)
    pa2.setCorrelated()
    pa3.convolve(pa2)
    np.testing.assert_allclose(pa3.x, conv_x)
    np.testing.assert_allclose(pa3.y, conv_y)
    np.testing.assert_allclose(pa3.flux, conv_flux)

    # But if both are correlated, then it's not this simple.
    pa3.assignAt(0, pa1)
    pa3.setCorrelated()
    assert pa3.isCorrelated()
    assert pa2.isCorrelated()
    pa3.convolve(pa2)
    with assert_raises(AssertionError):
        np.testing.assert_allclose(pa3.x, conv_x)
    with assert_raises(AssertionError):
        np.testing.assert_allclose(pa3.y, conv_y)
    np.testing.assert_allclose(np.sum(pa3.flux), 1.7*1.7)
    np.testing.assert_allclose(np.sum(pa3.x**2)/nphotons, 2*2.3**2, rtol=0.01)
    np.testing.assert_allclose(np.sum(pa3.y**2)/nphotons, 2*2.3**2, rtol=0.01)

    # Can also effect the convolution by treating the psf as a PhotonOp
    pa3.assignAt(0, pa1)
    pa3.setCorrelated()
    obj.applyTo(pa3, rng=rng2)
    np.testing.assert_allclose(pa3.x, conv_x)
    np.testing.assert_allclose(pa3.y, conv_y)
    np.testing.assert_allclose(pa3.flux, conv_flux)

    # Error to have different lengths
    pa4 = galsim.PhotonArray(50, pa1.x[:50], pa1.y[:50], pa1.flux[:50])
    assert_raises(galsim.GalSimError, pa1.convolve, pa4)


@timer
def test_wavelength_sampler():
    nphotons = 1000
    obj = galsim.Exponential(flux=1.7, scale_radius=2.3)
    rng = galsim.UniformDeviate(1234)

    photon_array = obj.shoot(nphotons, rng)

    sed = galsim.SED(os.path.join(sedpath, 'CWW_E_ext.sed'), 'A', 'flambda').thin()
    bandpass = galsim.Bandpass(os.path.join(bppath, 'LSST_r.dat'), 'nm').thin()

    sampler = galsim.WavelengthSampler(sed, bandpass)
    sampler.applyTo(photon_array, rng=rng)

    # Note: the underlying functionality of the sampleWavelengths function is tested
    # in test_sed.py.  So here we are really just testing that the wrapper class is
    # properly writing to the photon_array.wavelengths array.

    assert photon_array.hasAllocatedWavelengths()
    assert not photon_array.hasAllocatedAngles()

    do_pickle(sampler)

    print('mean wavelength = ',np.mean(photon_array.wavelength))
    print('min wavelength = ',np.min(photon_array.wavelength))
    print('max wavelength = ',np.max(photon_array.wavelength))

    assert np.min(photon_array.wavelength) > bandpass.blue_limit
    assert np.max(photon_array.wavelength) < bandpass.red_limit

    # This is a regression test based on the value at commit 134a119
    np.testing.assert_allclose(np.mean(photon_array.wavelength), 622.755128, rtol=1.e-4)

    # If we use a flat SED (in photons/nm), then the mean sampled wavelength should very closely
    # match the bandpass effective wavelength.
    photon_array2 = galsim.PhotonArray(100000)
    sed2 = galsim.SED('1', 'nm', 'fphotons')
    sampler2 = galsim.WavelengthSampler(sed2, bandpass)
    sampler2.applyTo(photon_array2, rng=rng)
    np.testing.assert_allclose(np.mean(photon_array2.wavelength),
                               bandpass.effective_wavelength,
                               rtol=0, atol=0.2,  # 2 Angstrom accuracy is pretty good
                               err_msg="Mean sampled wavelength not close to effective_wavelength")

    # If the photon array already has wavelengths set, then it proceeds, but gives a warning.
    with assert_warns(galsim.GalSimWarning):
        sampler2.applyTo(photon_array2, rng=rng)
    np.testing.assert_allclose(np.mean(photon_array2.wavelength),
                               bandpass.effective_wavelength, rtol=0, atol=0.2)

    # Test that using this as a surface op works properly.

    # First do the shooting and clipping manually.
    im1 = galsim.Image(64,64,scale=1)
    im1.setCenter(0,0)
    photon_array.flux[photon_array.wavelength < 600] = 0.
    photon_array.addTo(im1)

    # Make a dummy surface op that clips any photons with lambda < 600
    class Clip600(object):
        def applyTo(self, photon_array, local_wcs=None, rng=None):
            photon_array.flux[photon_array.wavelength < 600] = 0.

    # Use (a new) sampler and clip600 as photon_ops in drawImage
    im2 = galsim.Image(64,64,scale=1)
    im2.setCenter(0,0)
    clip600 = Clip600()
    rng2 = galsim.BaseDeviate(1234)
    sampler2 = galsim.WavelengthSampler(sed, bandpass)
    obj.drawImage(im2, method='phot', n_photons=nphotons, use_true_center=False,
                  photon_ops=[sampler2,clip600], rng=rng2, save_photons=True)
    print('sum = ',im1.array.sum(),im2.array.sum())
    np.testing.assert_array_equal(im1.array, im2.array)

    # Equivalent version just getting photons back
    rng2.seed(1234)
    photons = obj.makePhot(n_photons=nphotons, photon_ops=[sampler2,clip600], rng=rng2)
    print('phot.x = ',photons.x)
    print('im2.photons.x = ',im2.photons.x)
    assert photons == im2.photons

    # Base class is invalid to try to use.
    op = galsim.PhotonOp()
    with assert_raises(NotImplementedError):
        op.applyTo(photon_array)

@timer
def test_photon_angles():
    """Test the photon_array function
    """
    # Make a photon array
    seed = 12345
    ud = galsim.UniformDeviate(seed)
    gal = galsim.Sersic(n=4, half_light_radius=1)
    photon_array = gal.shoot(100000, ud)

    # Add the directions (N.B. using the same seed as for generating the photon array
    # above.  The fact that it is the same does not matter here; the testing routine
    # only needs to have a definite seed value so the consistency of the results with
    # expectations can be evaluated precisely
    fratio = 1.2
    obscuration = 0.2

    # rng can be None, an existing BaseDeviate, or an integer
    for rng in [ None, ud, 12345 ]:
        assigner = galsim.FRatioAngles(fratio, obscuration)
        assigner.applyTo(photon_array, rng=rng)

        do_pickle(assigner)

        dxdz = photon_array.dxdz
        dydz = photon_array.dydz

        phi = np.arctan2(dydz,dxdz)
        tantheta = np.sqrt(np.square(dxdz) + np.square(dydz))
        sintheta = np.sin(np.arctan(tantheta))

        # Check that the values are within the ranges expected
        # (The test on phi really can't fail, because it is only testing the range of the
        # arctan2 function.)
        np.testing.assert_array_less(-phi, np.pi, "Azimuth angles outside possible range")
        np.testing.assert_array_less(phi, np.pi, "Azimuth angles outside possible range")

        fov_angle = np.arctan(0.5 / fratio)
        obscuration_angle = obscuration * fov_angle
        np.testing.assert_array_less(-sintheta, -np.sin(obscuration_angle),
                                     "Inclination angles outside possible range")
        np.testing.assert_array_less(sintheta, np.sin(fov_angle),
                                     "Inclination angles outside possible range")

    # Compare these slopes with the expected distributions (uniform in azimuth
    # over all azimiths and uniform in sin(inclination) over the range of
    # allowed inclinations
    # Only test this for the last one, so we make sure we have a deterministic result.
    # (The above tests should be reliable even for the default rng.)
    phi_histo, phi_bins = np.histogram(phi, bins=100)
    sintheta_histo, sintheta_bins = np.histogram(sintheta, bins=100)
    phi_ref = float(np.sum(phi_histo))/phi_histo.size
    sintheta_ref = float(np.sum(sintheta_histo))/sintheta_histo.size

    chisqr_phi = np.sum(np.square(phi_histo - phi_ref)/phi_ref) / phi_histo.size
    chisqr_sintheta = np.sum(np.square(sintheta_histo - sintheta_ref) /
                             sintheta_ref) / sintheta_histo.size

    print('chisqr_phi = ',chisqr_phi)
    print('chisqr_sintheta = ',chisqr_sintheta)
    assert 0.9 < chisqr_phi < 1.1, "Distribution in azimuth is not nearly uniform"
    assert 0.9 < chisqr_sintheta < 1.1, "Distribution in sin(inclination) is not nearly uniform"

    # Try some invalid inputs
    assert_raises(ValueError, galsim.FRatioAngles, fratio=-0.3)
    assert_raises(ValueError, galsim.FRatioAngles, fratio=1.2, obscuration=-0.3)
    assert_raises(ValueError, galsim.FRatioAngles, fratio=1.2, obscuration=1.0)
    assert_raises(ValueError, galsim.FRatioAngles, fratio=1.2, obscuration=1.9)

@timer
def test_photon_io():
    """Test the ability to read and write photons to a file
    """
    nphotons = 1000

    obj = galsim.Exponential(flux=1.7, scale_radius=2.3)
    rng = galsim.UniformDeviate(1234)
    image = obj.drawImage(method='phot', n_photons=nphotons, save_photons=True, rng=rng)
    photons = image.photons
    assert photons.size() == len(photons) == nphotons

    with assert_raises(galsim.GalSimIncompatibleValuesError):
        obj.drawImage(method='phot', n_photons=nphotons, save_photons=True, maxN=1.e5)

    file_name = 'output/photons1.dat'
    photons.write(file_name)

    photons1 = galsim.PhotonArray.read(file_name)

    assert photons1.size() == nphotons
    assert not photons1.hasAllocatedWavelengths()
    assert not photons1.hasAllocatedAngles()

    np.testing.assert_array_equal(photons1.x, photons.x)
    np.testing.assert_array_equal(photons1.y, photons.y)
    np.testing.assert_array_equal(photons1.flux, photons.flux)

    sed = galsim.SED(os.path.join(sedpath, 'CWW_E_ext.sed'), 'nm', 'flambda').thin()
    bandpass = galsim.Bandpass(os.path.join(bppath, 'LSST_r.dat'), 'nm').thin()

    wave_sampler = galsim.WavelengthSampler(sed, bandpass)
    angle_sampler = galsim.FRatioAngles(1.3, 0.3)

    ops = [ wave_sampler, angle_sampler ]
    for op in ops:
        op.applyTo(photons, rng=rng)

    file_name = 'output/photons2.dat'
    photons.write(file_name)

    photons2 = galsim.PhotonArray.read(file_name)

    assert photons2.size() == nphotons
    assert photons2.hasAllocatedWavelengths()
    assert photons2.hasAllocatedAngles()

    np.testing.assert_array_equal(photons2.x, photons.x)
    np.testing.assert_array_equal(photons2.y, photons.y)
    np.testing.assert_array_equal(photons2.flux, photons.flux)
    np.testing.assert_array_equal(photons2.dxdz, photons.dxdz)
    np.testing.assert_array_equal(photons2.dydz, photons.dydz)
    np.testing.assert_array_equal(photons2.wavelength, photons.wavelength)

@timer
def test_dcr():
    """Test the dcr surface op
    """
    # This tests that implementing DCR with the surface op is equivalent to using
    # ChromaticAtmosphere.
    # We use fairly extreme choices for the parameters to make the comparison easier, so
    # we can still get good discrimination of any errors with only 10^6 photons.
    zenith_angle = 45 * galsim.degrees  # Larger angle has larger DCR.
    parallactic_angle = 129 * galsim.degrees  # Something random, not near 0 or 180
    pixel_scale = 0.03  # Small pixel scale means shifts are many pixels, rather than a fraction.
    alpha = -1.2  # The normal alpha is -0.2, so this is exaggerates the effect.

    bandpass = galsim.Bandpass('LSST_r.dat', 'nm')
    base_wavelength = bandpass.effective_wavelength
    base_wavelength += 500  # This exaggerates the effects fairly substantially.

    sed = galsim.SED('CWW_E_ext.sed', wave_type='ang', flux_type='flambda')

    flux = 1.e6
    base_PSF = galsim.Kolmogorov(fwhm=0.3)

    # Use ChromaticAtmosphere
    im1 = galsim.ImageD(50, 50, scale=pixel_scale)
    star = galsim.DeltaFunction() * sed
    star = star.withFlux(flux, bandpass=bandpass)
    chrom_PSF = galsim.ChromaticAtmosphere(base_PSF,
                                           base_wavelength=base_wavelength,
                                           zenith_angle=zenith_angle,
                                           parallactic_angle=parallactic_angle,
                                           alpha=alpha)
    chrom = galsim.Convolve(star, chrom_PSF)
    chrom.drawImage(bandpass, image=im1)

    # Use PhotonDCR
    im2 = galsim.ImageD(50, 50, scale=pixel_scale)
    dcr = galsim.PhotonDCR(base_wavelength=base_wavelength,
                           zenith_angle=zenith_angle,
                           parallactic_angle=parallactic_angle,
                           alpha=alpha)
    achrom = base_PSF.withFlux(flux)
    rng = galsim.BaseDeviate(31415)
    wave_sampler = galsim.WavelengthSampler(sed, bandpass)
    photon_ops = [wave_sampler, dcr]
    achrom.drawImage(image=im2, method='phot', rng=rng, photon_ops=photon_ops)

    do_pickle(dcr)

    im1 /= flux  # Divide by flux, so comparison is on a relative basis.
    im2 /= flux
    printval(im2, im1, show=False)
    np.testing.assert_almost_equal(im2.array, im1.array, decimal=4,
                                   err_msg="PhotonDCR didn't match ChromaticAtmosphere")

    # Use ChromaticAtmosphere in photon_ops
    im3 = galsim.ImageD(50, 50, scale=pixel_scale)
    photon_ops = [chrom_PSF]
    star.drawImage(bandpass, image=im3, method='phot', rng=rng, photon_ops=photon_ops)
    im3 /= flux
    printval(im3, im1, show=False)
    np.testing.assert_almost_equal(im3.array, im1.array, decimal=4,
                                   err_msg="ChromaticAtmosphere in photon_ops didn't match")

    # Repeat with thinned bandpass and SED to check that thin still works well.
    im3 = galsim.ImageD(50, 50, scale=pixel_scale)
    thin = 0.1  # Even higher also works.  But this is probably enough.
    thin_bandpass = bandpass.thin(thin)
    thin_sed = sed.thin(thin)
    print('len bp = %d => %d'%(len(bandpass.wave_list), len(thin_bandpass.wave_list)))
    print('len sed = %d => %d'%(len(sed.wave_list), len(thin_sed.wave_list)))
    wave_sampler = galsim.WavelengthSampler(thin_sed, thin_bandpass)
    photon_ops = [wave_sampler, dcr]
    achrom.drawImage(image=im3, method='phot', rng=rng, photon_ops=photon_ops)

    im3 /= flux
    printval(im3, im1, show=False)
    np.testing.assert_almost_equal(im3.array, im1.array, decimal=4,
                                   err_msg="thinning factor %f led to 1.e-4 level inaccuracy"%thin)

    # Check scale_unit
    im4 = galsim.ImageD(50, 50, scale=pixel_scale/60)
    dcr = galsim.PhotonDCR(base_wavelength=base_wavelength,
                           zenith_angle=zenith_angle,
                           parallactic_angle=parallactic_angle,
                           scale_unit='arcmin',
                           alpha=alpha)
    photon_ops = [wave_sampler, dcr]
    achrom.dilate(1./60).drawImage(image=im4, method='phot', rng=rng, photon_ops=photon_ops)
    im4 /= flux
    printval(im4, im1, show=False)
    np.testing.assert_almost_equal(im4.array, im1.array, decimal=4,
                                   err_msg="PhotonDCR with scale_unit=arcmin, didn't match")

    # Check some other valid options
    # alpha = 0 means don't do any size scaling.
    # obj_coord, HA and latitude are another option for setting the angles
    # pressure, temp, and water pressure are settable.
    # Also use a non-trivial WCS.
    wcs = galsim.FitsWCS('des_data/DECam_00154912_12_header.fits')
    image = galsim.Image(50, 50, wcs=wcs)
    bandpass = galsim.Bandpass('LSST_r.dat', wave_type='nm').thin(0.1)
    base_wavelength = bandpass.effective_wavelength
    lsst_lat = galsim.Angle.from_dms('-30:14:23.76')
    lsst_long = galsim.Angle.from_dms('-70:44:34.67')
    local_sidereal_time = 3.14 * galsim.hours  # Not pi. This is the time for this observation.

    im5 = galsim.ImageD(50, 50, wcs=wcs)
    obj_coord = wcs.toWorld(im5.true_center)
    base_PSF = galsim.Kolmogorov(fwhm=0.9)
    achrom = base_PSF.withFlux(flux)
    dcr = galsim.PhotonDCR(base_wavelength=bandpass.effective_wavelength,
                           obj_coord=obj_coord,
                           HA=local_sidereal_time-obj_coord.ra,
                           latitude=lsst_lat,
                           pressure=72,         # default is 69.328
                           temperature=290,     # default is 293.15
                           H2O_pressure=0.9)    # default is 1.067
                           #alpha=0)            # default is 0, so don't need to set it.
    photon_ops = [wave_sampler, dcr]
    achrom.drawImage(image=im5, method='phot', rng=rng, photon_ops=photon_ops)

    do_pickle(dcr)

    im6 = galsim.ImageD(50, 50, wcs=wcs)
    star = galsim.DeltaFunction() * sed
    star = star.withFlux(flux, bandpass=bandpass)
    chrom_PSF = galsim.ChromaticAtmosphere(base_PSF,
                                           base_wavelength=bandpass.effective_wavelength,
                                           obj_coord=obj_coord,
                                           HA=local_sidereal_time-obj_coord.ra,
                                           latitude=lsst_lat,
                                           pressure=72,
                                           temperature=290,
                                           H2O_pressure=0.9,
                                           alpha=0)
    chrom = galsim.Convolve(star, chrom_PSF)
    chrom.drawImage(bandpass, image=im6)

    im5 /= flux  # Divide by flux, so comparison is on a relative basis.
    im6 /= flux
    printval(im5, im6, show=False)
    np.testing.assert_almost_equal(im5.array, im6.array, decimal=3,
                                   err_msg="PhotonDCR with alpha=0 didn't match")

    # Use ChromaticAtmosphere in photon_ops
    im7 = galsim.ImageD(50, 50, wcs=wcs)
    photon_ops = [chrom_PSF]
    star.drawImage(bandpass, image=im7, method='phot', rng=rng, photon_ops=photon_ops)
    im7 /= flux
    printval(im7, im6, show=False)
    np.testing.assert_almost_equal(im7.array, im6.array, decimal=3,
                                   err_msg="ChromaticAtmosphere in photon_ops didn't match")

    # ChromaticAtmosphere in photon_ops is almost trivially equal to base_psf and dcr in photon_ops.
    im8 = galsim.ImageD(50, 50, wcs=wcs)
    photon_ops = [base_PSF, dcr]
    star.drawImage(bandpass, image=im8, method='phot', rng=rng, photon_ops=photon_ops)
    im8 /= flux
    printval(im8, im6, show=False)
    np.testing.assert_almost_equal(im8.array, im6.array, decimal=3,
                                   err_msg="base_psf + dcr in photon_ops didn't match")

    # Including the wavelength sampler with chromatic drawing is redundant.
    # This raises a warning, not an error.
    photon_ops = [wave_sampler, base_PSF, dcr]
    with assert_warns(galsim.GalSimWarning):
        star.drawImage(bandpass, image=im8, method='phot', rng=rng, photon_ops=photon_ops)
    im8 /= flux
    printval(im8, im6, show=False)
    np.testing.assert_almost_equal(im8.array, im6.array, decimal=3,
                                   err_msg="wave_sampler,base_psf,dcr in photon_ops didn't match")

    # Also check invalid parameters
    zenith_coord = galsim.CelestialCoord(13.54 * galsim.hours, lsst_lat)
    assert_raises(TypeError, galsim.PhotonDCR,
                  zenith_angle=zenith_angle,
                  parallactic_angle=parallactic_angle)  # base_wavelength is required
    assert_raises(TypeError, galsim.PhotonDCR,
                  base_wavelength=500,
                  parallactic_angle=parallactic_angle)  # zenith_angle (somehow) is required
    assert_raises(TypeError, galsim.PhotonDCR, 500,
                  zenith_angle=34.4,
                  parallactic_angle=parallactic_angle)  # zenith_angle must be Angle
    assert_raises(TypeError, galsim.PhotonDCR, 500,
                  zenith_angle=zenith_angle,
                  parallactic_angle=34.5)               # parallactic_angle must be Angle
    assert_raises(TypeError, galsim.PhotonDCR, 500,
                  obj_coord=obj_coord,
                  latitude=lsst_lat)                    # Missing HA
    assert_raises(TypeError, galsim.PhotonDCR, 500,
                  obj_coord=obj_coord,
                  HA=local_sidereal_time-obj_coord.ra)  # Missing latitude
    assert_raises(TypeError, galsim.PhotonDCR, 500,
                  obj_coord=obj_coord)                  # Need either zenith_coord, or (HA,lat)
    assert_raises(TypeError, galsim.PhotonDCR, 500,
                  obj_coord=obj_coord,
                  zenith_coord=zenith_coord,
                  HA=local_sidereal_time-obj_coord.ra)  # Can't have both HA and zenith_coord
    assert_raises(TypeError, galsim.PhotonDCR, 500,
                  obj_coord=obj_coord,
                  zenith_coord=zenith_coord,
                  latitude=lsst_lat)                    # Can't have both lat and zenith_coord
    assert_raises(TypeError, galsim.PhotonDCR, 500,
                  zenith_angle=zenith_angle,
                  parallactic_angle=parallactic_angle,
                  H20_pressure=1.)                      # invalid (misspelled)
    assert_raises(ValueError, galsim.PhotonDCR, 500,
                  zenith_angle=zenith_angle,
                  parallactic_angle=parallactic_angle,
                  scale_unit='inches')                  # invalid scale_unit
    photons = galsim.PhotonArray(2, flux=1)
    assert_raises(galsim.GalSimError, dcr.applyTo, photons) # Requires wavelengths to be set
    assert_raises(galsim.GalSimError, chrom_PSF.applyTo, photons) # Requires wavelengths to be set
    photons = galsim.PhotonArray(2, flux=1, wavelength=500)
    assert_raises(TypeError, dcr.applyTo, photons)      # Requires local_wcs

    # Invalid to use dcr without some way of setting wavelengths.
    assert_raises(galsim.GalSimError, achrom.drawImage, im2, method='phot', photon_ops=[dcr])

@unittest.skipIf(no_astroplan, 'Unable to import astroplan')
@timer
def test_dcr_angles():
    """Check the DCR angle calculations by comparing to astroplan's calculations of the same.
    """
    # Note: test_chromatic.py and test_sed.py both also test aspects of the dcr module, so
    # this particular test could belong in either of them too.  But I (MJ) put it here, since
    # I wrote it in conjunction with the tests of PhotonDCR to try to make sure that code
    # is working properly.
    import astropy.time

    # Set up an observation date, time, location, coordinate
    # These are arbitrary, so ripped from astroplan's docs
    # https://media.readthedocs.org/pdf/astroplan/latest/astroplan.pdf
    subaru = astroplan.Observer.at_site('subaru')
    time = astropy.time.Time('2015-06-16 12:00:00')

    # Stars that are visible from the north in summer time.
    names = ['Vega', 'Polaris', 'Altair', 'Regulus', 'Spica', 'Algol', 'Fomalhaut', 'Markab',
             'Deneb', 'Mizar', 'Dubhe', 'Sirius', 'Rigel', 'Alderamin']

    for name in names:
        try:
            star = astroplan.FixedTarget.from_name(name)
        except Exception as e:
            print('Caught exception trying to make star from name ',name)
            print(e)
            print('Aborting.  (Probably some kind of network problem.)')
            return
        print(star)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            ap_z = subaru.altaz(time, star).zen
            ap_q = subaru.parallactic_angle(time, star)
            local_sidereal_time = subaru.local_sidereal_time(time)
        print('According to astroplan:')
        print('  z,q = ', ap_z.deg, ap_q.deg)

        # Repeat with GalSim
        coord = galsim.CelestialCoord(star.ra.deg * galsim.degrees, star.dec.deg * galsim.degrees)
        lat = subaru.location.lat.deg * galsim.degrees
        ha = local_sidereal_time.deg * galsim.degrees - coord.ra
        zenith = galsim.CelestialCoord(local_sidereal_time.deg * galsim.degrees, lat)

        # Two ways to calculate it
        # 1. From coord, ha, lat
        z,q,_ = galsim.dcr.parse_dcr_angles(obj_coord=coord, HA=ha, latitude=lat)
        print('According to GalSim:')
        print('  z,q = ',z/galsim.degrees,q/galsim.degrees)

        np.testing.assert_almost_equal(
                z.rad, ap_z.rad, 2,
                "zenith angle doesn't agree with astroplan's calculation.")

        # Unfortunately, at least as of version 0.4, astroplan's parallactic angle calculation
        # has a bug.  It computes it as the arctan of some value, but doesn't use arctan2.
        # So whenever |q| > 90 degrees, it gets it wrong by 180 degrees.  Therefore, we only
        # test that tan(q) is right.  We'll check the quadrant below in test_dcr_moments().
        np.testing.assert_almost_equal(
                np.tan(q), np.tan(ap_q), 2,
                "parallactic angle doesn't agree with astroplan's calculation.")

        # 2. From coord, zenith_coord
        z,q,_ = galsim.dcr.parse_dcr_angles(obj_coord=coord, zenith_coord=zenith)
        print('  z,q = ',z/galsim.degrees,q/galsim.degrees)

        np.testing.assert_almost_equal(
                z.rad, ap_z.rad, 2,
                "zenith angle doesn't agree with astroplan's calculation.")
        np.testing.assert_almost_equal(
                np.tan(q), np.tan(ap_q), 2,
                "parallactic angle doesn't agree with astroplan's calculation.")

def test_dcr_moments():
    """Check that DCR gets the direction of the moment changes correct for some simple geometries.
    i.e. Basically check the sign conventions used in the DCR code.
    """
    # First, the basics.
    # 1. DCR shifts blue photons closer to zenith, because the index of refraction larger.
    #    cf. http://lsstdesc.github.io/chroma/
    # 2. Galsim models profiles as seen from Earth with North up (and therefore East left).
    # 3. Hour angle is negative when the object is in the east (soon after rising, say),
    #    zero when crossing the zenith meridian, and then positive to the west.

    # Use g-band, where the effect is more dramatic across the band than in redder bands.
    # Also use a reference wavelength significantly to the red, so there should be a net
    # overall shift towards zenith as well as a shear along the line to zenith.
    bandpass = galsim.Bandpass('LSST_g.dat', 'nm').thin(0.1)
    base_wavelength = 600  # > red end of g band

    # Uniform across the band is fine for this.
    sed = galsim.SED('1', wave_type='nm', flux_type='fphotons')
    rng = galsim.BaseDeviate(31415)
    wave_sampler = galsim.WavelengthSampler(sed, bandpass)

    star = galsim.Kolmogorov(fwhm=0.3, flux=1.e6)  # 10^6 photons should be enough.
    im = galsim.ImageD(50, 50, scale=0.05)  # Small pixel scale, so shift is many pixels.
    ra = 0 * galsim.degrees     # Completely irrelevant here.
    lat = -20 * galsim.degrees  # Also doesn't really matter much.

    # 1. HA < 0, Dec < lat  Spot should be shifted up and right.  e2 > 0.
    dcr = galsim.PhotonDCR(base_wavelength = base_wavelength,
                           HA = -2 * galsim.hours,
                           latitude = lat,
                           obj_coord = galsim.CelestialCoord(ra, lat - 20 * galsim.degrees))
    photon_ops = [wave_sampler, dcr]
    star.drawImage(image=im, method='phot', rng=rng, photon_ops=photon_ops)
    moments = galsim.utilities.unweighted_moments(im, origin=im.true_center)
    print('1. HA < 0, Dec < lat: ',moments)
    assert moments['My'] > 0   # up
    assert moments['Mx'] > 0   # right
    assert moments['Mxy'] > 0  # e2 > 0

    # 2. HA = 0, Dec < lat  Spot should be shifted up.  e1 < 0, e2 ~= 0.
    dcr = galsim.PhotonDCR(base_wavelength = base_wavelength,
                           HA = 0 * galsim.hours,
                           latitude = lat,
                           obj_coord = galsim.CelestialCoord(ra, lat - 20 * galsim.degrees))
    photon_ops = [wave_sampler, dcr]
    star.drawImage(image=im, method='phot', rng=rng, photon_ops=photon_ops)
    moments = galsim.utilities.unweighted_moments(im, origin=im.true_center)
    print('2. HA = 0, Dec < lat: ',moments)
    assert moments['My'] > 0   # up
    assert abs(moments['Mx']) < 0.05   # not left or right
    assert moments['Mxx'] < moments['Myy']  # e1 < 0
    assert abs(moments['Mxy']) < 0.1  # e2 ~= 0

    # 3. HA > 0, Dec < lat  Spot should be shifted up and left.  e2 < 0.
    dcr = galsim.PhotonDCR(base_wavelength = base_wavelength,
                           HA = 2 * galsim.hours,
                           latitude = lat,
                           obj_coord = galsim.CelestialCoord(ra, lat - 20 * galsim.degrees))
    photon_ops = [wave_sampler, dcr]
    star.drawImage(image=im, method='phot', rng=rng, photon_ops=photon_ops)
    moments = galsim.utilities.unweighted_moments(im, origin=im.true_center)
    print('3. HA > 0, Dec < lat: ',moments)
    assert moments['My'] > 0   # up
    assert moments['Mx'] < 0   # left
    assert moments['Mxy'] < 0  # e2 < 0

    # 4. HA < 0, Dec = lat  Spot should be shifted right.  e1 > 0, e2 ~= 0.
    dcr = galsim.PhotonDCR(base_wavelength = base_wavelength,
                           HA = -2 * galsim.hours,
                           latitude = lat,
                           obj_coord = galsim.CelestialCoord(ra, lat))
    photon_ops = [wave_sampler, dcr]
    star.drawImage(image=im, method='phot', rng=rng, photon_ops=photon_ops)
    moments = galsim.utilities.unweighted_moments(im, origin=im.true_center)
    print('4. HA < 0, Dec = lat: ',moments)
    assert abs(moments['My']) < 1.   # not up or down  (Actually slightly down in the south.)
    assert moments['Mx'] > 0   # right
    assert moments['Mxx'] > moments['Myy']  # e1 > 0
    assert abs(moments['Mxy']) < 2.  # e2 ~= 0  (Actually slightly negative because of curvature.)

    # 5. HA = 0, Dec = lat  Spot should not be shifted.  e1 ~= 0, e2 ~= 0.
    dcr = galsim.PhotonDCR(base_wavelength = base_wavelength,
                           HA = 0 * galsim.hours,
                           latitude = lat,
                           obj_coord = galsim.CelestialCoord(ra, lat))
    photon_ops = [wave_sampler, dcr]
    star.drawImage(image=im, method='phot', rng=rng, photon_ops=photon_ops)
    moments = galsim.utilities.unweighted_moments(im, origin=im.true_center)
    print('5. HA = 0, Dec = lat: ',moments)
    assert abs(moments['My']) < 0.05   # not up or down
    assert abs(moments['Mx']) < 0.05   # not left or right
    assert abs(moments['Mxx'] - moments['Myy']) < 0.1  # e1 ~= 0
    assert abs(moments['Mxy']) < 0.1  # e2 ~= 0

    # 6. HA > 0, Dec = lat  Spot should be shifted left.  e1 > 0, e2 ~= 0.
    dcr = galsim.PhotonDCR(base_wavelength = base_wavelength,
                           HA = 2 * galsim.hours,
                           latitude = lat,
                           obj_coord = galsim.CelestialCoord(ra, lat))
    photon_ops = [wave_sampler, dcr]
    star.drawImage(image=im, method='phot', rng=rng, photon_ops=photon_ops)
    moments = galsim.utilities.unweighted_moments(im, origin=im.true_center)
    print('6. HA > 0, Dec = lat: ',moments)
    assert abs(moments['My']) < 1.   # not up or down  (Actually slightly down in the south.)
    assert moments['Mx'] < 0   # left
    assert moments['Mxx'] > moments['Myy']  # e1 > 0
    assert abs(moments['Mxy']) < 2.  # e2 ~= 0  (Actually slgihtly positive because of curvature.)

    # 7. HA < 0, Dec > lat  Spot should be shifted down and right.  e2 < 0.
    dcr = galsim.PhotonDCR(base_wavelength = base_wavelength,
                           HA = -2 * galsim.hours,
                           latitude = lat,
                           obj_coord = galsim.CelestialCoord(ra, lat + 20 * galsim.degrees))
    photon_ops = [wave_sampler, dcr]
    star.drawImage(image=im, method='phot', rng=rng, photon_ops=photon_ops)
    moments = galsim.utilities.unweighted_moments(im, origin=im.true_center)
    print('7. HA < 0, Dec > lat: ',moments)
    assert moments['My'] < 0   # down
    assert moments['Mx'] > 0   # right
    assert moments['Mxy'] < 0  # e2 < 0

    # 8. HA = 0, Dec > lat  Spot should be shifted down.  e1 < 0, e2 ~= 0.
    dcr = galsim.PhotonDCR(base_wavelength = base_wavelength,
                           HA = 0 * galsim.hours,
                           latitude = lat,
                           obj_coord = galsim.CelestialCoord(ra, lat + 20 * galsim.degrees))
    photon_ops = [wave_sampler, dcr]
    star.drawImage(image=im, method='phot', rng=rng, photon_ops=photon_ops)
    moments = galsim.utilities.unweighted_moments(im, origin=im.true_center)
    print('8. HA = 0, Dec > lat: ',moments)
    assert moments['My'] < 0   # down
    assert abs(moments['Mx']) < 0.05   # not left or right
    assert moments['Mxx'] < moments['Myy']  # e1 < 0
    assert abs(moments['Mxy']) < 0.1  # e2 ~= 0

    # 9. HA > 0, Dec > lat  Spot should be shifted down and left.  e2 > 0.
    dcr = galsim.PhotonDCR(base_wavelength = base_wavelength,
                           HA = 2 * galsim.hours,
                           latitude = lat,
                           obj_coord = galsim.CelestialCoord(ra, lat + 20 * galsim.degrees))
    photon_ops = [wave_sampler, dcr]
    star.drawImage(image=im, method='phot', rng=rng, photon_ops=photon_ops)
    moments = galsim.utilities.unweighted_moments(im, origin=im.true_center)
    print('9. HA > 0, Dec > lat: ',moments)
    assert moments['My'] < 0   # down
    assert moments['Mx'] < 0   # left
    assert moments['Mxy'] > 0  # e2 > 0


@timer
def test_refract():
    ud = galsim.UniformDeviate(57721)
    for _ in range(1000):
        photon_array = galsim.PhotonArray(1000, flux=1)
        ud.generate(photon_array.dxdz)
        ud.generate(photon_array.dydz)
        photon_array.dxdz *= 1.2  # -0.6 to 0.6
        photon_array.dydz *= 1.2
        photon_array.dxdz -= 0.6
        photon_array.dydz -= 0.6
        # copy for testing later
        dxdz0 = np.array(photon_array.dxdz)
        dydz0 = np.array(photon_array.dydz)
        index_ratio = ud()*4+0.25  # 0.25 to 4.25
        refract = galsim.Refraction(index_ratio)
        refract.applyTo(photon_array)

        do_pickle(refract)

        # Triangle is length 1 in the z direction and length sqrt(dxdz**2+dydz**2)
        # in the 'r' direction.
        rsqr0 = dxdz0**2 + dydz0**2
        sintheta0 = np.sqrt(rsqr0)/np.sqrt(1+rsqr0)
        # See if total internal reflection applies
        w = sintheta0 < index_ratio
        np.testing.assert_array_equal(photon_array.dxdz[~w], np.nan)
        np.testing.assert_array_equal(photon_array.dydz[~w], np.nan)
        np.testing.assert_array_equal(
            photon_array.flux,
            np.where(w, 1.0, 0.0)
        )

        sintheta0 = sintheta0[w]
        dxdz0 = dxdz0[w]
        dydz0 = dydz0[w]
        dxdz1 = photon_array.dxdz[w]
        dydz1 = photon_array.dydz[w]
        rsqr1 = dxdz1**2 + dydz1**2
        sintheta1 = np.sqrt(rsqr1)/np.sqrt(1+rsqr1)
        # Check Snell's law
        np.testing.assert_allclose(sintheta0, index_ratio*sintheta1)

        # Check azimuthal angle stays constant
        phi0 = np.arctan2(dydz0, dxdz0)
        phi1 = np.arctan2(dydz1, dxdz1)
        np.testing.assert_allclose(phi0, phi1)

        # Check plane of refraction is perpendicular to (0,0,1)
        np.testing.assert_allclose(
            np.dot(
                np.cross(
                    np.stack([dxdz0, dydz0, -np.ones(len(dxdz0))], axis=1),
                    np.stack([dxdz1, dydz1, -np.ones(len(dxdz1))], axis=1),
                ),
                [0,0,1]
            ),
            0.0,
            rtol=0, atol=1e-13
        )

    # Try a wavelength dependent index_ratio
    index_ratio = lambda w: np.where(w < 1, 1.1, 2.2)
    photon_array = galsim.PhotonArray(100)
    ud.generate(photon_array.wavelength)
    ud.generate(photon_array.dxdz)
    ud.generate(photon_array.dydz)
    photon_array.dxdz *= 1.2  # -0.6 to 0.6
    photon_array.dydz *= 1.2
    photon_array.dxdz -= 0.6
    photon_array.dydz -= 0.6
    photon_array.wavelength *= 2  # 0 to 2
    dxdz0 = photon_array.dxdz.copy()
    dydz0 = photon_array.dydz.copy()

    refract_func = galsim.Refraction(index_ratio=index_ratio)
    refract_func.applyTo(photon_array)
    dxdz_func = photon_array.dxdz.copy()
    dydz_func = photon_array.dydz.copy()

    photon_array.dxdz = dxdz0.copy()
    photon_array.dydz = dydz0.copy()
    refract11 = galsim.Refraction(index_ratio=1.1)
    refract11.applyTo(photon_array)
    dxdz11 = photon_array.dxdz.copy()
    dydz11 = photon_array.dydz.copy()

    photon_array.dxdz = dxdz0.copy()
    photon_array.dydz = dydz0.copy()
    refract22 = galsim.Refraction(index_ratio=2.2)
    refract22.applyTo(photon_array)
    dxdz22 = photon_array.dxdz.copy()
    dydz22 = photon_array.dydz.copy()

    w = photon_array.wavelength < 1
    np.testing.assert_allclose(
        dxdz_func,
        np.where(w, dxdz11, dxdz22)
    )
    np.testing.assert_allclose(
        dydz_func,
        np.where(w, dydz11, dydz22)
    )


@timer
def test_focus_depth():
    bd = galsim.BaseDeviate(1234)
    for _ in range(100):
        # Test that FocusDepth is additive
        photon_array = galsim.PhotonArray(1000)
        photon_array2 = galsim.PhotonArray(1000)
        photon_array.x = 0.0
        photon_array.y = 0.0
        photon_array2.x = 0.0
        photon_array2.y = 0.0
        galsim.FRatioAngles(1.234, obscuration=0.606).applyTo(photon_array, rng=bd)
        photon_array2.dxdz[:] = photon_array.dxdz
        photon_array2.dydz[:] = photon_array.dydz
        fd1 = galsim.FocusDepth(1.1)
        fd2 = galsim.FocusDepth(2.2)
        fd3 = galsim.FocusDepth(3.3)
        fd1.applyTo(photon_array)
        fd2.applyTo(photon_array)
        fd3.applyTo(photon_array2)

        do_pickle(fd1)

        np.testing.assert_allclose(photon_array.x, photon_array2.x, rtol=0, atol=1e-15)
        np.testing.assert_allclose(photon_array.y, photon_array2.y, rtol=0, atol=1e-15)
        # Assuming focus is at x=y=0, then
        #   intrafocal (depth < 0) => (x > 0 => dxdz < 0)
        #   extrafocal (depth > 0) => (x > 0 => dxdz > 0)
        # We applied an extrafocal operation above, so check for corresponding
        # relation between x, dxdz
        np.testing.assert_array_less(0, photon_array.x * photon_array.dxdz)

        # transforming by depth and -depth is null
        fd4 = galsim.FocusDepth(-3.3)
        fd4.applyTo(photon_array)
        np.testing.assert_allclose(photon_array.x, 0.0, rtol=0, atol=1e-15)
        np.testing.assert_allclose(photon_array.y, 0.0, rtol=0, atol=1e-15)

    # Check that invalid photon array is trapped
    pa = galsim.PhotonArray(10)
    fd = galsim.FocusDepth(1.0)
    with np.testing.assert_raises(galsim.GalSimError):
        fd.applyTo(pa)

    # Check that we can infer depth from photon positions before and after...
    for _ in range(100):
        photon_array = galsim.PhotonArray(1000)
        photon_array2 = galsim.PhotonArray(1000)
        ud = galsim.UniformDeviate(bd)
        ud.generate(photon_array.x)
        ud.generate(photon_array.y)
        photon_array.x -= 0.5
        photon_array.y -= 0.5
        galsim.FRatioAngles(1.234, obscuration=0.606).applyTo(photon_array, rng=bd)
        photon_array2.x[:] = photon_array.x
        photon_array2.y[:] = photon_array.y
        photon_array2.dxdz[:] = photon_array.dxdz
        photon_array2.dydz[:] = photon_array.dydz
        depth = ud()-0.5
        galsim.FocusDepth(depth).applyTo(photon_array2)
        np.testing.assert_allclose((photon_array2.x - photon_array.x)/photon_array.dxdz, depth)
        np.testing.assert_allclose((photon_array2.y - photon_array.y)/photon_array.dydz, depth)
        np.testing.assert_allclose(photon_array.dxdz, photon_array2.dxdz)
        np.testing.assert_allclose(photon_array.dydz, photon_array2.dydz)


@timer
def test_lsst_y_focus():
    # Check that applying reasonable focus depth (from O'Connor++06) indeed leads to smaller spot
    # size for LSST y-band.
    rng = galsim.BaseDeviate(9876543210)
    bandpass = galsim.Bandpass("LSST_y.dat", wave_type='nm')
    sed = galsim.SED("1", wave_type='nm', flux_type='flambda')
    obj = galsim.Gaussian(fwhm=1e-5)
    oversampling = 32
    photon_ops0 = [
        galsim.WavelengthSampler(sed, bandpass),
        galsim.FRatioAngles(1.234, 0.606),
        galsim.FocusDepth(0.0),
        galsim.Refraction(3.9)
    ]
    img0 = obj.drawImage(
        sensor=galsim.SiliconSensor(),
        method='phot',
        n_photons=100000,
        photon_ops=photon_ops0,
        scale=0.2/oversampling,
        nx=32*oversampling,
        ny=32*oversampling,
        rng=rng
    )
    T0 = img0.calculateMomentRadius()
    T0 *= 10*oversampling/0.2  # arcsec => microns

    # O'Connor finds minimum spot size when the focus depth is ~ -12 microns.  Our sensor isn't
    # necessarily the same as the one there though; our minimum seems to be around -6 microns.
    # That could be due to differences in the design of the sensor though.  We just use -6 microns
    # here, which is still useful to test the sign of the `depth` parameter and the interaction of
    # the 4 different surface operators required to produce this effect, and is roughly consistent
    # with O'Connor.

    depth1 = -6.  # microns, negative means surface is intrafocal
    depth1 /= 10  # microns => pixels
    photon_ops1 = [
        galsim.WavelengthSampler(sed, bandpass),
        galsim.FRatioAngles(1.234, 0.606),
        galsim.FocusDepth(depth1),
        galsim.Refraction(3.9)
    ]
    img1 = obj.drawImage(
        sensor=galsim.SiliconSensor(),
        method='phot',
        n_photons=100000,
        photon_ops=photon_ops1,
        scale=0.2/oversampling,
        nx=32*oversampling,
        ny=32*oversampling,
        rng=rng
    )
    T1 = img1.calculateMomentRadius()
    T1 *= 10*oversampling/0.2  # arcsec => microns
    np.testing.assert_array_less(T1, T0)


@timer
def test_fromArrays():
    """Check that fromArrays constructor catches errors and never copies."""

    rng = galsim.BaseDeviate(123)

    x = np.empty(1000)
    y = np.empty(1000)
    flux = np.empty(1000)

    Nsplit = 444

    pa_batch = galsim.PhotonArray.fromArrays(x, y, flux)
    pa_1 = galsim.PhotonArray.fromArrays(
        x[:Nsplit],
        y[:Nsplit],
        flux[:Nsplit]
    )
    pa_2 = galsim.PhotonArray.fromArrays(
        x[Nsplit:],
        y[Nsplit:],
        flux[Nsplit:]
    )

    assert pa_batch.x is x
    assert pa_batch.y is y
    assert pa_batch.flux is flux
    np.testing.assert_array_equal(pa_batch.x, x)
    np.testing.assert_array_equal(pa_batch.y, y)
    np.testing.assert_array_equal(pa_batch.flux, flux)
    np.testing.assert_array_equal(pa_1.x, pa_batch.x[:Nsplit])
    np.testing.assert_array_equal(pa_1.y, pa_batch.y[:Nsplit])
    np.testing.assert_array_equal(pa_1.flux, pa_batch.flux[:Nsplit])
    np.testing.assert_array_equal(pa_2.x, pa_batch.x[Nsplit:])
    np.testing.assert_array_equal(pa_2.y, pa_batch.y[Nsplit:])
    np.testing.assert_array_equal(pa_2.flux, pa_batch.flux[Nsplit:])

    # Do some manipulation and check views are still equivalent
    obj1 = galsim.Gaussian(fwhm=0.1)*64
    obj2 = galsim.Kolmogorov(fwhm=0.2)*23

    obj1._shoot(pa_1, rng)
    obj2._shoot(pa_2, rng)

    assert pa_batch.x is x
    assert pa_batch.y is y
    assert pa_batch.flux is flux
    np.testing.assert_array_equal(pa_batch.x, x)
    np.testing.assert_array_equal(pa_batch.y, y)
    np.testing.assert_array_equal(pa_batch.flux, flux)
    np.testing.assert_array_equal(pa_1.x, pa_batch.x[:Nsplit])
    np.testing.assert_array_equal(pa_1.y, pa_batch.y[:Nsplit])
    np.testing.assert_array_equal(pa_1.flux, pa_batch.flux[:Nsplit])
    np.testing.assert_array_equal(pa_2.x, pa_batch.x[Nsplit:])
    np.testing.assert_array_equal(pa_2.y, pa_batch.y[Nsplit:])
    np.testing.assert_array_equal(pa_2.flux, pa_batch.flux[Nsplit:])

    # Add some optional args and apply PhotonOps to the batch this time.
    dxdz = np.empty(1000)
    dydz = np.empty(1000)
    wavelength = np.empty(1000)
    pa_batch = galsim.PhotonArray.fromArrays(x, y, flux, dxdz, dydz, wavelength)
    pa_1 = galsim.PhotonArray.fromArrays(
        x[:Nsplit],
        y[:Nsplit],
        flux[:Nsplit],
        dxdz[:Nsplit],
        dydz[:Nsplit],
        wavelength[:Nsplit]
    )
    pa_2 = galsim.PhotonArray.fromArrays(
        x[Nsplit:],
        y[Nsplit:],
        flux[Nsplit:],
        dxdz[Nsplit:],
        dydz[Nsplit:],
        wavelength[Nsplit:]
    )

    sed = galsim.SED("vega.txt", wave_type='nm', flux_type='flambda')
    bp = galsim.Bandpass("LSST_r.dat", wave_type='nm')
    with assert_warns(galsim.GalSimWarning):
        galsim.WavelengthSampler(sed, bp).applyTo(pa_batch, rng=rng)
    galsim.FRatioAngles(1.2, 0.61).applyTo(pa_batch, rng=rng)

    assert pa_batch.x is x
    assert pa_batch.y is y
    assert pa_batch.flux is flux
    assert pa_batch.dxdz is dxdz
    assert pa_batch.dydz is dydz
    assert pa_batch.wavelength is wavelength
    np.testing.assert_array_equal(pa_batch.x, x)
    np.testing.assert_array_equal(pa_batch.y, y)
    np.testing.assert_array_equal(pa_batch.flux, flux)
    np.testing.assert_array_equal(pa_batch.dxdz, dxdz)
    np.testing.assert_array_equal(pa_batch.dydz, dydz)
    np.testing.assert_array_equal(pa_batch.wavelength, wavelength)
    np.testing.assert_array_equal(pa_1.x, pa_batch.x[:Nsplit])
    np.testing.assert_array_equal(pa_1.y, pa_batch.y[:Nsplit])
    np.testing.assert_array_equal(pa_1.flux, pa_batch.flux[:Nsplit])
    np.testing.assert_array_equal(pa_1.dxdz, pa_batch.dxdz[:Nsplit])
    np.testing.assert_array_equal(pa_1.dydz, pa_batch.dydz[:Nsplit])
    np.testing.assert_array_equal(pa_1.wavelength, pa_batch.wavelength[:Nsplit])
    np.testing.assert_array_equal(pa_2.x, pa_batch.x[Nsplit:])
    np.testing.assert_array_equal(pa_2.y, pa_batch.y[Nsplit:])
    np.testing.assert_array_equal(pa_2.flux, pa_batch.flux[Nsplit:])
    np.testing.assert_array_equal(pa_2.dxdz, pa_batch.dxdz[Nsplit:])
    np.testing.assert_array_equal(pa_2.dydz, pa_batch.dydz[Nsplit:])
    np.testing.assert_array_equal(pa_2.wavelength, pa_batch.wavelength[Nsplit:])

    # Check the is_corr flag gets set
    assert not pa_batch.isCorrelated()
    pa_batch = galsim.PhotonArray.fromArrays(x, y, flux, dxdz, dydz, wavelength, is_corr=True)
    assert pa_batch.isCorrelated()

    # Check some invalid inputs are caught
    with np.testing.assert_raises(TypeError):
        galsim.PhotonArray.fromArrays(list(x), y, flux, dxdz, dydz, wavelength)
    with np.testing.assert_raises(TypeError):
        galsim.PhotonArray.fromArrays(np.empty(1000, dtype=int), y, flux, dxdz, dydz, wavelength)
    with np.testing.assert_raises(ValueError):
        galsim.PhotonArray.fromArrays(x[:10], y, flux, dxdz, dydz, wavelength)
    with np.testing.assert_raises(ValueError):
        galsim.PhotonArray.fromArrays(np.empty(2000)[::2], y, flux, dxdz, dydz, wavelength)


if __name__ == '__main__':
    testfns = [v for k, v in vars().items() if k[:5] == 'test_' and callable(v)]
    if no_astroplan:
        print('Skipping test_dcr_angles, since astroplan not installed.')
        testfns.remove(test_dcr_angles)
    for testfn in testfns:
        testfn()
