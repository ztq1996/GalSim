/* -*- c++ -*-
 * Copyright (c) 2012-2021 by the GalSim developers team on GitHub
 * https://github.com/GalSim-developers
 *
 * This file is part of GalSim: The modular galaxy image simulation toolkit.
 * https://github.com/GalSim-developers/GalSim
 *
 * GalSim is free software: redistribution and use in source and binary forms,
 * with or without modification, are permitted provided that the following
 * conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions, and the disclaimer given in the accompanying LICENSE
 *    file.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions, and the disclaimer given in the documentation
 *    and/or other materials provided with the distribution.
 */
// This just includes the relevant header files from the galsim directory.

#ifndef GalSim_H
#define GalSim_H

// The basic SBProfile stuff:
#include "galsim/SBProfile.h"
#include "galsim/SBDeconvolve.h"
#include "galsim/SBInterpolatedImage.h"

// An interface for dealing with images
#include "galsim/Image.h"

// Noise stuff
#include "galsim/Random.h"

// An integration package by Mike Jarvis
#include "galsim/integ/Int.h"

// Adaptive moments code by Hirata, Seljak, and Mandelbaum
#include "galsim/hsm/PSFCorr.h"

// Version information.
// Note: This file is automatically generated by SCons using the current version info.
#include "galsim/Version.h"

#endif
