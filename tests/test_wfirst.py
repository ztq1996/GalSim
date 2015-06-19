# Copyright (c) 2012-2015 by the GalSim developers team on GitHub
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
"""Unit tests for the WFIRST module (galsim.wfirst)
"""

import numpy as np

from galsim_test_helpers import *

try:
    import galsim
    import galsim.wfirst
except ImportError:
    import os
    import sys
    path, filename = os.path.split(__file__)
    sys.path.append(os.path.abspath(os.path.join(path, "..")))
    import galsim
    import galsim.wfirst

def test_wfirst_wcs():
    """Test the WFIRST WCS routines against those from software provided by WFIRST project office.
    """
    import time
    t1 = time.time()

    # The standard against which we will compare is the output of some software provided by Jeff
    # Kruk.  The files used here were generated by Rachel on her Macbook using the script in
    # wfirst_files/make_standards.sh, and none of the parameters below can be changed without
    # modifying and rerunning that script.  We use 4 sky positions and rotation angles (2 defined
    # using the focal plane array, 2 using the observatory coordinates), and in each case, use a
    # different SCA for our tests.  We will simply read in the stored WCS and generate new ones, and
    # check that they have the right value of SCA center and pixel scale at the center, and that if
    # we offset by 500 pixels in some direction that gives the same sky position in each case.
    ra_test = [127., 307.4, -61.52, 0.0]
    dec_test = [-70., 50., 22.7, 0.0]
    pa_test = [160., 79., 23.4, -3.1]
    sca_test = [2, 13, 7, 18]
    import datetime
    ve = datetime.datetime(2025,3,20,9,2,0)
    date_test = [ve, ve, ve, datetime.date(2025,6,20)]
    pa_is_fpa_test = [True, False, True, False]

    dist_arcsec = []
    dist_2_arcsec = []
    pix_area_ratio = []
    for i_test in range(len(ra_test)):
        # Make the WCS for this test.
        world_pos = galsim.CelestialCoord(ra_test[i_test]*galsim.degrees,
                                          dec_test[i_test]*galsim.degrees)
        if i_test == 0:
            # Just for this case, we want to get the WCS for all SCAs.  This will enable some
            # additional tests that we don't do for the other test case.
            gs_wcs_dict = galsim.wfirst.getWCS(PA=pa_test[i_test]*galsim.degrees,
                                               world_pos=world_pos,
                                               PA_is_FPA=pa_is_fpa_test[i_test],
                                               date=date_test[i_test])
            np.testing.assert_equal(
                len(gs_wcs_dict), galsim.wfirst.n_sca,
                err_msg='WCS dict has wrong length: %d vs. %d'%(len(gs_wcs_dict),
                                                                galsim.wfirst.n_sca))
        else:
            # Use the SCAs keyword to just get the WCS for the SCA that we want.
            gs_wcs_dict = galsim.wfirst.getWCS(PA=pa_test[i_test]*galsim.degrees,
                                               world_pos=world_pos,
                                               PA_is_FPA=pa_is_fpa_test[i_test],
                                               SCAs=sca_test[i_test],
                                               date=date_test[i_test])
            np.testing.assert_equal(
                len(gs_wcs_dict), 1,
                err_msg='WCS dict has wrong length: %d vs. %d'%(len(gs_wcs_dict), 1))

        # Read in reference.
        test_file = 'test%d_sca_%02d.fits'%(i_test+1, sca_test[i_test])
        ref_wcs = galsim.FitsWCS(os.path.join('wfirst_files',test_file))

        gs_wcs = gs_wcs_dict[sca_test[i_test]]

        # Check center position:
        im_cent_pos = galsim.PositionD(galsim.wfirst.n_pix/2., galsim.wfirst.n_pix/2)
        ref_cent_pos = ref_wcs.toWorld(im_cent_pos)
        gs_cent_pos = gs_wcs.toWorld(im_cent_pos)
        dist_arcsec.append(ref_cent_pos.distanceTo(gs_cent_pos) / galsim.arcsec)

        # Check pixel area
        rat = ref_wcs.pixelArea(image_pos=im_cent_pos)/gs_wcs.pixelArea(image_pos=im_cent_pos)
        pix_area_ratio.append(rat-1.)

        # Check another position, just in case rotations are messed up.
        im_other_pos = galsim.PositionD(im_cent_pos.x+500., im_cent_pos.y-200.)
        ref_other_pos = ref_wcs.toWorld(im_other_pos)
        gs_other_pos = gs_wcs.toWorld(im_other_pos)
        dist_2_arcsec.append(ref_other_pos.distanceTo(gs_other_pos) / galsim.arcsec)

        if i_test == 0:
            # For just one of our tests cases, we'll do some additional tests.  These will target
            # the findSCA() functionality.  First, we'll choose an SCA and check that its center is
            # found to be in that SCA.
            found_sca = galsim.wfirst.findSCA(gs_wcs_dict, gs_cent_pos)
            np.testing.assert_equal(found_sca, sca_test[i_test],
                                    err_msg='Did not find SCA center position to be on that SCA!')

            # Then, we go to a place that should be off the side by a tiny bit, and check that it is
            # NOT on an SCA if we exclude borders, but IS on the SCA if we include borders.
            im_off_edge_pos = galsim.PositionD(-2., galsim.wfirst.n_pix/2.)
            world_off_edge_pos = gs_wcs.toWorld(im_off_edge_pos)
            found_sca = galsim.wfirst.findSCA(gs_wcs_dict, world_off_edge_pos)
            assert found_sca is None
            found_sca = galsim.wfirst.findSCA(gs_wcs_dict, world_off_edge_pos, include_border=True)
            np.testing.assert_equal(found_sca, sca_test[i_test],
                                    err_msg='Did not find slightly off-edge position on the SCA'
                                    ' when including borders!')

    np.testing.assert_array_less(
        np.array(dist_arcsec),
        np.ones(len(ra_test))*galsim.wfirst.pixel_scale/100, 
        err_msg='For at least one WCS, center offset from reference was > 0.01(pixel scale).')
    np.testing.assert_array_less(
        np.array(dist_2_arcsec),
        np.ones(len(ra_test))*galsim.wfirst.pixel_scale/100, 
        err_msg='For at least one WCS, other offset from reference was > 0.01(pixel scale).')
    np.testing.assert_array_less(
        np.array(pix_area_ratio),
        np.ones(len(ra_test))*0.0001,
        err_msg='For at least one WCS, pixel areas differ from reference by >0.01%.')

    # Check whether we're allowed to look at certain positions on certain dates.
    # Let's choose RA=90 degrees, dec=10 degrees.
    # We know that it's best to look about 90 degrees from the Sun.  So on the vernal and autumnal
    # equinox, this should be a great place to look, but not midway in between.  We'll use
    # approximate dates for these.
    pos = galsim.CelestialCoord(90.*galsim.degrees, 10.*galsim.degrees)
    import datetime
    assert galsim.wfirst.allowedPos(pos, datetime.date(2025,3,20))
    assert galsim.wfirst.allowedPos(pos, datetime.date(2025,9,20))
    assert not galsim.wfirst.allowedPos(pos, datetime.date(2025,6,20))

    # Finally make sure it does something reasonable for the observatory position angle.
    # When the sun is at (0,0), and we look at (90,0), then +Z points towards the Sun and +Y points
    # North, giving a PA of 0 degrees.
    pos = galsim.CelestialCoord(90.*galsim.degrees, 0.*galsim.degrees)
    test_date = datetime.datetime(2025,3,20,9,2)
    pa = galsim.wfirst.bestPA(pos, test_date)
    np.testing.assert_almost_equal(pa.rad(), 0., decimal=3)
    # Now make it look at the same RA as the sun but quite different declination.  It wants +Z
    # pointing North toward Sun, so we'll get a -90 degree angle for the PA.
    pos = galsim.CelestialCoord(0.*galsim.degrees, -70.*galsim.degrees)
    pa = galsim.wfirst.bestPA(pos, test_date)
    np.testing.assert_almost_equal(pa.rad(), -np.pi/2, decimal=3)

    t2 = time.time()
    print 'time for %s = %.2f'%(funcname(),t2-t1)

def test_wfirst_backgrounds():
    """Test the WFIRST background estimation routines for basic sanity.
    """
    import time
    import datetime
    t1 = time.time()

    # The routine should not allow us to look directly at the sun since the background there is high
    # (to understate the problem).  If no date is supplied, then the routine assumes RA=dec=0 means
    # we are looking at the sun.
    bp_dict = galsim.wfirst.getBandpasses()
    bp = bp_dict['J129'] # one of the standard filters, doesn't really matter which
    try:
        np.testing.assert_raises(ValueError, galsim.wfirst.getSkyLevel, bp,
                                 world_pos=galsim.CelestialCoord(0.*galsim.degrees,
                                                                 0.*galsim.degrees))
        # near autumn equinox
        np.testing.assert_raises(ValueError, galsim.wfirst.getSkyLevel, bp,
                                 world_pos=galsim.CelestialCoord(180.*galsim.degrees,
                                                                 5.*galsim.degrees),
                                 date=datetime.date(2025,9,15))
    except ImportError:
        print 'The assert_raises tests require nose'

    # The routine should have some obvious symmetry, for example, ecliptic latitude above vs. below
    # plane and ecliptic longitude positive vs. negative (or vs. 360 degrees - original value).
    # Because of how equatorial and ecliptic coordinates are related on the adopted date, we can do
    # this test as follows:
    test_ra = 50.*galsim.degrees
    test_dec = 10.*galsim.degrees
    test_pos_p = galsim.CelestialCoord(test_ra, test_dec)
    test_pos_m = galsim.CelestialCoord(-1.*(test_ra/galsim.degrees)*galsim.degrees, 
                                        -1.*(test_dec/galsim.degrees)*galsim.degrees)
    level_p = galsim.wfirst.getSkyLevel(bp, world_pos=test_pos_p)
    level_m = galsim.wfirst.getSkyLevel(bp, world_pos=test_pos_m)
    np.testing.assert_almost_equal(level_m, level_p, decimal=8)

    # The routine should handle an input exposure time sensibly.  Our original level_p was in
    # e-/arcsec^2 using the WFIRST exposure time.  We will define another exposure time, pass it in,
    # and confirm that the output is consistent with this.
    level_p_2 = galsim.wfirst.getSkyLevel(bp, world_pos=test_pos_p,
                                          exptime=1.7*galsim.wfirst.exptime)
    np.testing.assert_almost_equal(1.7*level_p, level_p_2, decimal=8)

    t2 = time.time()
    print 'time for %s = %.2f'%(funcname(),t2-t1)

def test_wfirst_bandpass():
    """Test the WFIRST bandpasses for basic sanity.
    """
    import time
    t1 = time.time()
    from galsim._pyfits import pyfits

    # Obtain the bandpasses with AB_zeropoint set
    exp_time = 200. # non WFIRST exposure time
    bp = galsim.wfirst.getBandpasses(AB_zeropoint=True, exptime=exp_time)

    # Check if the zeropoints have been set correctly
    AB_spec = lambda x: (3631e-23)*exp_time*(np.pi)*(100.**2)*\
              (galsim.wfirst.diameter**2)*(1-galsim.wfirst.obscuration**2)/4.
    AB_sed = galsim.SED(spec=AB_spec,flux_type='fnu')
    for filter_name, filter_ in bp.iteritems():
        mag = AB_sed.calculateMagnitude(bandpass=filter_)
        np.testing.assert_almost_equal(mag,0.0,decimal=6,
            err_msg="Zeropoint not set accurately enough for bandpass filter \
            {0}".format(filter_name))

    # Do a slightly less trivial check of bandpass-related calculations:
    # Jeff Kruk (at Goddard) took an SED template from the Castelli-Kurucz library, normalized it to
    # a particular magnitude in SDSS g band, and checked the count rates he expects for the WFIRST
    # bands.  I (RM) independently did the same calculation (downloading the templates and bandpass
    # myself and using GalSim for all the important bits of the calculation) and my results agree a
    # the 5% level.  Given that I didn't quite have the same SED, we were very happy with this level
    # of agreement.  The unit test below reproduces this test, and requires agreement at the 10%
    # level.
    # Jeff used the C-K template with solar metallicity, T=9550K, surface gravity logg=3.95.  I
    # downloaded a grid of templates and just used the nearest one, which has solar metallicity,
    # T=9500K, surface gravity logg=4.0.
    sed_data = pyfits.getdata(os.path.join('wfirst_files','ckp00_9500.fits'))
    lam = sed_data.WAVELENGTH.astype(np.float64)
    t = sed_data.g40.astype(np.float64)
    sed_tab = galsim.LookupTable(x=lam, f=t, interpolant='linear')
    sed = galsim.SED(sed_tab, wave_type='A')

    # Now take the SDSS g bandpass:
    gfile =  '/Users/rmandelb/Downloads/g.dat'
    bp_dat = np.loadtxt(os.path.join('wfirst_files','g.dat')).transpose()
    bp_tab = galsim.LookupTable(x=bp_dat[0,:], f=bp_dat[1,:], interpolant='linear')
    bp_ref = galsim.Bandpass(bp_tab, wave_type='A')
    # Set an AB zeropoint using WFIRST params:
    eff_diam = 100.*galsim.wfirst.diameter*np.sqrt(1.-galsim.wfirst.obscuration**2)
    bp_ref = bp_ref.withZeropoint('AB', effective_diameter=eff_diam, exptime=galsim.wfirst.exptime)
    # Now get a new SED that has magnitude -0.093 in this filter, since that's the normalization
    # that Jeff imposed for his tests.
    sed = sed.withMagnitude(-0.093, bp_ref)

    # Reference count rates, from Jeff:
    reference = {}
    reference['Z087'] = 1.98e10
    reference['Y106'] = 1.97e10
    reference['J129'] = 1.52e10
    reference['H158'] = 1.11e10
    reference['F184'] = 0.58e10
    reference['W149'] = 4.34e10

    # Only 10% accuracy required because did not use quite the same stellar template.  Fortunately,
    # bugs can easily lead to orders of magnitude errors, so this unit test is still pretty
    # non-trivial.
    for filter_name, filter_ in bp.iteritems():
        flux = sed.calculateFlux(filter_)
        count_rate = flux / galsim.wfirst.exptime
        np.testing.assert_allclose(
            count_rate, reference[filter_name], rtol=0.1,
            err_msg="Count rate for stellar model not as expected for bandpass "
            "{0}".format(filter_name))

    t2 = time.time()
    print 'time for %s = %.2f'%(funcname(),t2-t1)

def test_wfirst_detectors():
    """Test the WFIRST detector routines for consistency with standard detector routines.
    """
    import time
    t1 = time.time()

    # This seems almost silly, but for now the WFIRST detector routines are define in terms of the
    # standard GalSim detector routines, and we should check that even if the routines are modified,
    # they still can agree given the same inputs.
    # So start by making a fairly simple image.
    obj = galsim.Gaussian(sigma=3.*galsim.wfirst.pixel_scale, flux=1.e5)
    im = obj.drawImage(scale=galsim.wfirst.pixel_scale)

    # Make copies that we transform using both sets of routines, and check for consistency.
    # First we do nonlinearity:
    im_1 = im.copy()
    im_2 = im.copy()
    im_1.applyNonlinearity(NLfunc=galsim.wfirst.NLfunc)
    galsim.wfirst.applyNonlinearity(im_2)
    assert im_2.scale == im_1.scale
    assert im_2.wcs == im_1.wcs
    assert im_2.dtype == im_1.dtype
    assert im_2.bounds == im_1.bounds
    np.testing.assert_array_equal(
        im_2.array, im_1.array,
        err_msg='Nonlinearity results depend on function used.')

    # Then we do reciprocity failure:
    im_1 = im.copy()
    im_2 = im.copy()
    im_1.addReciprocityFailure(exp_time=galsim.wfirst.exptime,
                               alpha=galsim.wfirst.reciprocity_alpha,
                               base_flux=1.0)
    galsim.wfirst.addReciprocityFailure(im_2)
    assert im_2.scale == im_1.scale
    assert im_2.wcs == im_1.wcs
    assert im_2.dtype == im_1.dtype
    assert im_2.bounds == im_1.bounds
    np.testing.assert_array_equal(
        im_2.array, im_1.array,
        err_msg='Reciprocity failure results depend on function used.')

    # Then we do IPC:
    im_1 = im.copy()
    im_2 = im.copy()
    im_1.applyIPC(IPC_kernel=galsim.wfirst.ipc_kernel, kernel_normalization=True)
    galsim.wfirst.applyIPC(im_2)
    assert im_2.scale == im_1.scale
    assert im_2.wcs == im_1.wcs
    assert im_2.dtype == im_1.dtype
    assert im_2.bounds == im_1.bounds
    np.testing.assert_array_equal(
        im_2.array, im_1.array,
        err_msg='IPC results depend on function used.')

    t2 = time.time()
    print 'time for %s = %.2f'%(funcname(),t2-t1)

def test_wfirst_psfs():
    """Test the WFIRST PSF routines for reasonable behavior.
    """
    import time
    t1 = time.time()

    # The WFIRST PSF routines can take a long time under some circumstances.  For example, storing
    # images for interpolation can be expensive, particularly when using the full pupil plane
    # functionality.  To speed up our calculations, we will limit the unit tests to certain
    # situations:
    # - fully chromatic PSFs without interpolation and without loading the pupil plane image.  But
    #   then we just want to play with the objects in a fast way (e.g., evaluating at one
    #   wavelength, not integrating over a bandpass).
    # - fully chromatic PSFs with interpolation, but only interpolating between two wavelengths.
    # - achromatic PSFs without loading the pupil plane image.

    # First test: check that if we don't specify SCAs, then we get all the expected ones.
    wfirst_psfs = galsim.wfirst.getPSF(approximate_struts=True)
    got_scas = np.array(wfirst_psfs.keys())
    expected_scas = np.arange(1, galsim.wfirst.n_sca+1, 1)
    np.testing.assert_array_equal(
        got_scas, expected_scas,
        err_msg='List of SCAs was not as expected when using defaults.')

    # Check that if we specify SCAs, then we get the ones we specified.
    expected_scas = [5, 7, 14]
    wfirst_psfs = galsim.wfirst.getPSF(SCAs=expected_scas,
                                       approximate_struts=True)
    got_scas = wfirst_psfs.keys()
    # Have to sort it in numerical order for this comparison.
    got_scas.sort()
    got_scas = np.array(got_scas)
    np.testing.assert_array_equal(
        got_scas, expected_scas, err_msg='List of SCAs was not as requested')

    # Check that if we specify a particular wavelength, the PSF that is drawn is the same as if we
    # had gotten chromatic PSFs and then used evaluateAtWavelength.  Note that this nominally seems
    # like a test of the chromatic functionality, but there are ways that getPSF() could mess up
    # inputs such that there is a disagreement.  That's why this unit test belongs here.
    use_sca = 5
    use_lam = 900. # nm
    wfirst_psfs_chrom = galsim.wfirst.getPSF(SCAs=use_sca,
                                             approximate_struts=True)
    psf_chrom = wfirst_psfs_chrom[use_sca]
    wfirst_psfs_achrom = galsim.wfirst.getPSF(SCAs=use_sca,
                                              approximate_struts=True,
                                              wavelength=use_lam)
    psf_achrom = wfirst_psfs_achrom[use_sca]
    # First, we can draw the achromatic PSF.
    im_achrom = psf_achrom.drawImage(scale=galsim.wfirst.pixel_scale)
    im_chrom = im_achrom.copy()
    obj_chrom = psf_chrom.evaluateAtWavelength(use_lam)
    im_chrom = obj_chrom.drawImage(image=im_chrom, scale=galsim.wfirst.pixel_scale)
    # Normalization should probably not be right.
    im_chrom *= im_achrom.array.sum()/im_chrom.array.sum()
    # But otherwise these images should agree *extremely* well.
    np.testing.assert_array_almost_equal(
        im_chrom.array, im_achrom.array, decimal=8,
        err_msg='PSF at a given wavelength and chromatic one evaluated at that wavelength disagree.')

    # Make a very limited check that interpolation works: just 2 wavelengths, 1 SCA.
    # Note that the limits below are the blue and red limits for the Y106 filter.
    blue_limit = 900. # nm
    red_limit = 1230. # nm
    n_waves = 2
    other_sca = 12
    wfirst_psfs_int = galsim.wfirst.getPSF(SCAs=[use_sca, other_sca],
                                           approximate_struts=True, n_waves=2,
                                           wavelength_limits=(blue_limit, red_limit))
    psf_int = wfirst_psfs_int[use_sca]
    # Check that evaluation at the edge wavelength, which we used for previous test, is consistent
    # with previous results.
    im_int = im_achrom.copy()
    obj_int = psf_int.evaluateAtWavelength(use_lam)
    im_int = obj_int.drawImage(image=im_int, scale=galsim.wfirst.pixel_scale)
    # These images should agree well, but not perfectly.  One of them comes from drawing an image
    # from an object directly, whereas the other comes from drawing an image of that object, making
    # it into an InterpolatedImage, then re-drawing it.
    np.testing.assert_array_almost_equal(
        im_int.array, im_achrom.array, decimal=4,
        err_msg='PSF at a given wavelength and interpolated chromatic one evaluated at that '
        'wavelength disagree.')

    # Below are some more expensive tests that will run only when running test_wfirst.py directly,
    # but not when doing "scons tests"
    if __name__ == "__main__":
        # Check that if we store and reload, what we get back is consistent with what we put in.
        test_file = 'tmp_store.fits'
        # Make sure we clear out any old versions
        import os
        if os.path.exists(test_file):
            os.remove(test_file)
        full_bp_list = galsim.wfirst.getBandpasses()
        bp_list = ['Y106']
        galsim.wfirst.storePSFImages(bandpass_list=bp_list, PSF_dict=wfirst_psfs_int,
                                     filename=test_file)
        new_dict = galsim.wfirst.loadPSFImages(test_file)
        # Check that it contains the right list of bandpasses.
        np.testing.assert_array_equal(
            new_dict.keys(), bp_list, err_msg='Wrong list of bandpasses in stored file')
        # Check that when we take the dict for that bandpass, we get the right list of SCAs.
        np.testing.assert_array_equal(
            new_dict[bp_list[0]].keys(), wfirst_psfs_int.keys(),
            err_msg='Wrong list of SCAs in stored file')
        # Now draw an image from the stored object.
        img_stored = new_dict[bp_list[0]][other_sca].drawImage(scale=1.3*galsim.wfirst.pixel_scale)
        # Make a comparable image from the original interpolated object.  This requires convolving with
        # a star that has a flat SED.
        star = galsim.Gaussian(sigma=1.e-8, flux=1.)
        star_sed = galsim.SED(lambda x:1).withFlux(1, full_bp_list[bp_list[0]])
        obj = galsim.Convolve(wfirst_psfs_int[other_sca], star*star_sed)
        test_im = img_stored.copy()
        test_im = obj.drawImage(full_bp_list[bp_list[0]],
                                image=test_im, scale=1.3*galsim.wfirst.pixel_scale)
        # We have made some approximations here, so we cannot expect it to be great.
        # Request 1% accuracy.
        np.testing.assert_array_almost_equal(
            img_stored.array, test_im.array, decimal=2,
            err_msg='PSF from stored file and actual PSF object disagree.')

        # Delete test files when done.
        os.remove(test_file)

    # Check for exceptions if we:
    # (1) Include optional aberrations in an unacceptable form.
    # (2) Invalid SCA numbers.
    try:
        np.testing.assert_raises(ValueError, galsim.wfirst.getPSF,
                                 extra_aberrations=[0.03, -0.06])
        np.testing.assert_raises(ValueError, galsim.wfirst.getPSF,
                                 SCAs=30)
        np.testing.assert_raises(ValueError, galsim.wfirst.getPSF,
                                 SCAs=0)
    except ImportError:
        print 'The assert_raises tests require nose'

    t2 = time.time()
    print 'time for %s = %.2f'%(funcname(),t2-t1)

if __name__ == "__main__":
    test_wfirst_wcs()
    test_wfirst_backgrounds()
    test_wfirst_bandpass()
    test_wfirst_detectors()
    test_wfirst_psfs()

