"""
@file random.py 
Addition of docstrings to the Random deviate classes at the Python layer and definition of the 
DistDeviate class.
"""
from . import _galsim

def permute(rng, *args):
    """Randomly permute one or more lists.

    If more than one list is given, then all lists will have the same random permutation 
    applied to it.

    @param rng    The random number generator to use. (This will be converted to a UniformDeviate.)
    @param args   Any number of lists to be permuted.
    """
    ud = _galsim.UniformDeviate(rng)
    if len(args) == 0: return

    # We use an algorithm called the Knuth shuffle, which is based on the Fisher-Yates shuffle.
    # See http://en.wikipedia.org/wiki/Fisher-Yates_shuffle for more information.
    n = len(args[0])
    for i in range(n-1,1,-1):
        j = int((i+1) * ud())
        if j == i+1: j = i  # I'm not sure if this is possible, but just in case...
        for list in args:
            list[i], list[j] = list[j], list[i]


class DistDeviate:
    """A class to draw random numbers from a user-defined probability distribution.
    
    DistDeviate, unlike other galsim Deviates, is NOT an instance of the BaseDeviate class.  It
    has the same methods as those objects, but it cannot be used to initialize other BaseDeviates
    and it will not satisfy isinstance checks for BaseDeviate.  However, DistDeviate includes an 
    internal UniformDeviate, _ud, which can be used to initialize other BaseDeviates if necessary.
    
    Initialization
    --------------
    
    Some sample initialization calls:
    
    >>> d = galsim.random.DistDeviate(list1,list2)
    # Initializes d to be a DistDeviate using the distribution P(x), where x is list1 and P(x) is
    # list2, and seeds the PRNG using current time. The lists can also be tuples or numpy arrays.
    
    >>> d = galsim.random.DistDeviate(f,min=min,max=max)   
    # Initializes d to be a DistDeviate instance with a distribution given by the callable function
    # f(x) from x=min to x=max and seeds the PRNG using current time.  When a function is passed, 
    # the keywords min and max are required.
    
    >>> d = galsim.random.DistDeviate(filename,1062533)
    # Initializes d to be a DistDeviate instance with a distribution given by the data in file
    # filename, which must be a 2-column ASCII table, and seeds the PRNG using the long int 
    # seed 1062533.
    
    >>> d = galsim.random.DistDeviate(list1,list2,dev,interpolant='linear')
    # Initializes d to be a DistDeviate instance using the distribution given by list1 and list2,
    # using linear interpolation to get probabilities for intermediate points, and seeds the
    # PRNG using the BaseDeviate dev.

       @param min          The minimum desired return value (required if a callable function is passed)
       @param max          The maximum desired return value (required if a callable function is passed)
       @param interpolant  Type of interpolation used for interpolating (x,p) or filename (causes an
                           error if passed alongside a callable function). Options are given in the
                           documentation for galsim.LookupTable.  (default: 'spline')
       @param npoints      Number of points in the internal interpolation (default: 256)

    Calling
    -------
    Taking the instance from the above examples, successive calls to d() then generate pseudo-random
    numbers distributed according to the initialized distribution.

    >>> d = galsim.random.DistDeviate([1.,2.,3.],[1.,2.,3.])
    >>> d()
    >>> d()            
"""    
    def __init__(self, *args, **kwargs):
        """Initializes a DistDeviate instance.
        
        The first unnamed argument(s) must be a filename, callable function, or two one-dimensional
        lists, numpy arrays, or tuples.  The second unnamed argument, if given, must be something
        that can initialize a BaseDeviate instance, such as another BaseDeviate or a long int seed.
        
        """
        
        import numpy
        import galsim
        npoints=kwargs.pop('npoints',256)
 
        if not args:
            raise TypeError("Too few unnamed arguments to initialize DistDeviate")
        if hasattr(args[0],'__call__'):
            userfunction=args[0]
            filename=args[0] #for later error messages
            narg=1
            if 'min' in kwargs and 'max' in kwargs:
                xmin=kwargs.pop('min',0.)
                xmax=kwargs.pop('max',1.)
                if xmax<=xmin:
                    raise ValueError("Max value passed to DistDeviate is <= min value")
            else:
                raise TypeError(
                    "DistDeviate called with a function must include min and max keywords")
        #If the first argument isn't callable, see if it's a list or filename (which have
        #some setup in common, hence the else rather than elif)
        else:
            interpolant=kwargs.pop('interpolant','spline')
            if isinstance(args[0],(list,tuple,numpy.ndarray)):
                filename=args[0] #just for later error outputs
                if len(args)>1 and isinstance(args[1],(list,tuple,numpy.ndarray)):
                    userfunction=galsim.LookupTable(args[0],args[1],interpolant=interpolant)
                    narg=2
                    xmin=min(args[0])
                    xmax=max(args[0])
                else:
                    raise TypeError('Only one list or array passed to DistDeviate: %s'%args[0])
            #If none of the above work, assume the unnamed argument is a filename
            elif isinstance(args[0], basestring):
                filename=args[0]
                userfunction=galsim.LookupTable(file=filename,interpolant=interpolant)
                xmin=min(userfunction.getArgs())
                xmax=max(userfunction.getArgs())
                narg=1
            else:
                raise TypeError("Unnamed arguments to DistDeviate are not of permitted types")
            xmin=kwargs.pop('min',xmin)
            xmax=kwargs.pop('max',xmax)
            if xmax<=xmin:
                raise ValueError('Max value <= min value in DistDeviate')

        #Set up the random number generator and check the number of arguments.
        if len(args)==narg+1:
            self._ud=galsim.UniformDeviate(args[narg])
        elif len(args)==narg:
            self._ud=galsim.UniformDeviate()
        else:
            raise TypeError("Too many unnamed arguments to DistDeviate")
        if kwargs:
            raise TypeError("Keyword arguments to DistDeviate not permitted: %s"%kwargs.keys())

        dx=(1.*xmax-xmin)/(npoints-1)
        xarray=xmin+dx*numpy.array(range(npoints),float)
        cumulativeprobability=[]
        for i in range(xarray.shape[0]):
            cumulativeprobability.append(dx*numpy.sum(xarray[0:i]))
        cumulativeprobability=numpy.array(cumulativeprobability)
        #Check that cumulativeprobability is always increasing or always decreasing
        #and if it isn't, either tweak it to fix or return an error.
        if not numpy.all(cumulativeprobability>=0):
            raise ValueError('Negative probability passed to DistDeviate: %s'%filename)
        dx=numpy.diff(cumulativeprobability)
        if not numpy.all(dx >=0.):
            #This check plus the cumulativeprobability>=0 should capture any nonzero probabilities
            raise ValueError('Cumulative probability in DistDeviate is not monotonic')
        elif not numpy.all(dx > 0.):
            #Remove consecutive dx=0 points, except endpoints
            zeroindex=numpy.squeeze(numpy.where(dx==0))
            dindexright=numpy.squeeze(numpy.where(numpy.diff(zeroindex)==1))
            dindexleft=numpy.squeeze(numpy.where(numpy.diff(zeroindex[1:])==1))
            removearray=dindexleft[numpy.in1d(dindexleft,dindexright)]
            cumulativeprobability=numpy.delete(cumulativeprobability,removearray)
            dx=numpy.diff(cumulativeprobability)
            #Tweak the edges of dx=0 regions so function is always increasing
            for index in squeeze(numpy.where(dx == 0)):
                if index+2<len(cumulativeprobability):
                   cumulativeprobability[index+1]+=0.0001*(
                       cumulativeprobability[index+2]-cumulativeprobability[index+1])
                else:
                   cumulativeprobability=cumulativeprobability[:-1]
                   xarray=xarray[:-1]
            dx=numpy.diff(cumulativeprobability)
            if not (numpy.all(dx>0)):
                raise RuntimeError(
                    'Cumulative probability in DistDeviate is too flat for program to fix')
                        
        #Quietly renormalize the probability if it wasn't already normalized
        cumulativeprobability/=cumulativeprobability[-1]
        self._inverseprobabilitytable=galsim.LookupTable(cumulativeprobability,xarray,
                                                         interpolant='spline')


    def __call__(self):
        return self._inverseprobabilitytable(self._ud())
    
    def applyTo(self, image):
    	import numpy
        shp=image.array.shape
        image.array[:,:]+=numpy.array([[self() for col in range(shp[1])] for row in range(shp[0])])
    
        
    def seed(self,arg=None):
    	if arg is None:
    		self._ud()
    	else:
	        self._ud.seed(arg)
    
    def reset(self,arg=None):
    	if arg is None:
    		self._ud()
    	else:
        	self._ud.reset(arg)


# BaseDeviate docstrings
_galsim.BaseDeviate.__doc__ = """
Base class for all the various random deviates.

This holds the essential random number generator that all the other classes use.

All deviates have three constructors that define different ways of setting up the random number
generator.

  1) Only the arguments particular to the derived class (e.g. mean and sigma for GaussianDeviate).
     In this case, a new random number generator is created and it is seeded using the computer's
     microsecond counter.

  2) Using a particular seed as the first argument to the constructor.
     This will also create a new random number generator, but seed it with the provided value.

  3) Passing another BaseDeviate as the first arguemnt to the constructor.
     This will make the new Deviate share the same underlying random number generator with the other
     Deviate.  So you can make one Deviate (of any type), and seed it with a particular
     deterministic value.  Then if you pass that Deviate to any other one you make, they will all be
     using the same RNG and have a particular deterministic series of values.  (It doesn't have to
     be the first one -- any one you've made later can also be used to seed a new one.)
     
There is not much you can do with something that is only known to be a BaseDeviate rather than one
of the derived classes other than construct it and change the seed, and use it as an argument to
pass to other Deviate constructors.

Examples
--------

    >>> rng = galsim.BaseDeviate(215324)    
    >>> rng()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    TypeError: 'BaseDeviate' object is not callable
    >>> ud = galsim.UniformDeviate(rng)
    >>> ud()
    0.58736140513792634
    >>> ud2 = galsim.UniformDeviate(215324)
    >>> ud2()
    0.58736140513792634

"""

_galsim.BaseDeviate.seed.__func__.__doc__ = """
Seed the pseudo-random number generator.

Multiple Calling Options
------------------------

    >>> galsim.BaseDeviate.seed()       # Re-seed the PRNG using current time.

    >>> galsim.BaseDeviate.seed(lseed)  # Re-seed the PRNG using specified seed, where lseed is a
                                        # long int.

"""

_galsim.BaseDeviate.reset.__func__.__doc__ = """
Reset the pseudo-random number generator, severing connections to any other deviates.

Multiple Calling Options
------------------------

    >>> galsim.BaseDeviate.reset()        # Re-seed the PRNG using current time, and sever the
                                          # connection to any other Deviate.

    >>> galsim.BaseDeviate.reset(lseed)   # Re-seed the PRNG using specified seed, where lseed is a
                                          # long int, and sever the connection to any other Deviate.

    >>> galsim.BaseDeviate.reset(dev)     # Re-connect this Deviate with the same underlying random
                                          # number generator supplied in dev.

"""


# UniformDeviate docstrings
_galsim.UniformDeviate.__doc__ = """
Pseudo-random number generator with uniform distribution in interval [0.,1.).

Initialization
--------------

    >>> u = galsim.UniformDeviate()       # Initializes u to be a UniformDeviate instance, and seeds
                                          # the PRNG using current time.

    >>> u = galsim.UniformDeviate(lseed)  # Initializes u to be a UniformDeviate instance, and seeds
                                          # the PRNG using specified long integer lseed.

    >>> u = galsim.UniformDeviate(dev)    # Initializes u to be a UniformDeviate instance, and share
                                          # the same underlying random number generator as dev.

Calling
-------
Taking the instance from the above examples, successive calls to u() then generate pseudo-random
numbers distributed uniformly in the interval [0., 1.).

    >>> u = galsim.UniformDeviate()
    >>> u()
    0.35068059829063714
    >>> u()            
    0.56841182382777333

Methods
-------
To add deviates to every element of an image, use the syntax image.addNoise(u).

This docstring can be found using the Python interpreter or in pysrc/Random.cpp.
"""

_galsim.UniformDeviate.applyTo.__func__.__doc__ = """
Add Uniform deviates to every element in a supplied Image.

Calling
-------

    >>> galsim.UniformDeviate.applyTo(image)  

On output each element of the input Image will have a pseudo-random UniformDeviate return value 
added to it.

To add deviates to every element of an image, the syntax image.addNoise() is preferred.
"""
_galsim.UniformDeviate.__call__.__func__.__doc__= "Draw a new random number from the distribution."


# GaussianDeviate docstrings
_galsim.GaussianDeviate.__doc__ = """
Pseudo-random number generator with Gaussian distribution.

See http://en.wikipedia.org/wiki/Gaussian_distribution for further details.

Initialization
--------------

    >>> g = galsim.GaussianDeviate(mean=0., sigma=1.)          # Initializes g to be a
                                                               # GaussianDeviate instance using the
                                                               # current time for the seed.

    >>> g = galsim.GaussianDeviate(lseed, mean=0., sigma=1.)   # Initializes g using the specified
                                                               # seed, where lseed is a long int.

    >>> g = galsim.GaussianDeviate(dev, mean=0., sigma=1.)     # Initializes g to share the same
                                                               # underlying random number generator
                                                               # as dev.

Parameters:

    mean     optional mean for Gaussian distribution [default `mean = 0.`].
    sigma    optional sigma for Gaussian distribution [default `sigma = 1.`].  Must be > 0.

Calling
-------
Taking the instance from the above examples, successive calls to g() then generate pseudo-random
numbers which Gaussian-distributed with the provided mean, sigma.

    >>> g = galsim.GaussianDeviate()
    >>> g()
    1.398768034960607
    >>> g()
    -0.8456136323830128

Methods
-------
To add deviates to every element of an image, use the syntax image.addNoise(g).

To get and set the deviate parameters, see the docstrings for the .getMean(), .setMean(), 
.getSigma() and .setSigma() methods of each instance.
"""

_galsim.GaussianDeviate.applyTo.__func__.__doc__ = """
Add Gaussian deviates to every element in a supplied Image.

Calling
-------

    >>> galsim.GaussianDeviate.applyTo(image)

On output each element of the input Image will have a pseudo-random GaussianDeviate return value 
added to it, with current values of mean and sigma.

To add deviates to every element of an image, the syntax image.addNoise() is preferred.
"""

_galsim.GaussianDeviate.__call__.__func__.__doc__ = """
Draw a new random number from the distribution.

Returns a Gaussian deviate with current mean and sigma.
"""
_galsim.GaussianDeviate.getMean.__func__.__doc__ = "Get current distribution mean."
_galsim.GaussianDeviate.setMean.__func__.__doc__ = "Set current distribution mean."
_galsim.GaussianDeviate.getSigma.__func__.__doc__ = "Get current distribution sigma."
_galsim.GaussianDeviate.setSigma.__func__.__doc__ = "Set current distribution sigma."


# BinomialDeviate docstrings
_galsim.BinomialDeviate.__doc__ = """
Pseudo-random Binomial deviate for N trials each of probability p.

N is number of 'coin flips,' p is probability of 'heads,' and each call returns an integer value
where 0 <= value <= N giving number of heads.  See http://en.wikipedia.org/wiki/Binomial_distribution
for more information.

Initialization
--------------

    >>> b = galsim.BinomialDeviate(N=1., p=0.5)          # Initializes b to be a BinomialDeviate
                                                         # instance using the current time for the
                                                         # seed.

    >>> b = galsim.BinomialDeviate(lseed, N=1., p=0.5)   # Initializes b using the specified seed,
                                                         # where lseed is a long int.

    >>> b = galsim.BinomialDeviate(dev, N=1., p=0.5)     # Initializes b to share the same
                                                         # underlying random number generator as dev.

Parameters:

    N   optional number of 'coin flips' per trial [default `N = 1`].  Must be > 0.
    p   optional probability of success per coin flip [default `p = 0.5`].  Must be > 0.

Calling
-------
Taking the instance from the above examples, successive calls to b() then generate pseudo-random
numbers binomial-distributed with the provided N, p.

    >>> b = galsim.BinomialDeviate()
    >>> b()
    0
    >>> b()
    1

Methods
-------
To add deviates to every element of an image, use the syntax image.addNoise(b).

To get and set the deviate parameters, see the docstrings for the .getN(), .setN(), .getP() and
.setP() methods of each instance.
"""

_galsim.BinomialDeviate.applyTo.__func__.__doc__ = """
Add Binomial deviates to every element in a supplied Image.

Calling
-------

    >>> galsim.BinomialDeviate.applyTo(image)    

On output each element of the input Image will have a pseudo-random BinomialDeviate return value 
added to it, with current values of N and p.

To add deviates to every element of an image, the syntax image.addNoise() is preferred.
"""

_galsim.BinomialDeviate.__call__.__func__.__doc__ = """
Draw a new random number from the distribution.

Returns a Binomial deviate with current N and p.
"""
_galsim.BinomialDeviate.getN.__func__.__doc__ = "Get current distribution N."
_galsim.BinomialDeviate.setN.__func__.__doc__ = "Set current distribution N."
_galsim.BinomialDeviate.getP.__func__.__doc__ = "Get current distribution p."
_galsim.BinomialDeviate.setP.__func__.__doc__ = "Set current distribution p."


# PoissonDeviate docstrings
_galsim.PoissonDeviate.__doc__ = """
Pseudo-random Poisson deviate with specified mean.

The input mean sets the mean and variance of the Poisson deviate.  An integer deviate with this
distribution is returned after each call.  See http://en.wikipedia.org/wiki/Poisson_distribution
for more details.

Initialization
--------------

    >>> p = galsim.PoissonDeviate(mean=1.)         # Initializes g to be a PoissonDeviate instance
                                                   # using the current time for the seed.

    >>> p = galsim.PoissonDeviate(lseed, mean=1.)  # Initializes g using the specified seed, where
                                                   # lseed is a long int.

    >>> p = galsim.PoissonDeviate(dev, mean=1.)    # Initializes g to share the same underlying
                                                   # random number generator as dev.

Parameters:

    mean     optional mean of the distribution [default `mean = 1`].  Must be > 0.

Calling
-------
Taking the instance from the above examples, successive calls to p() will return successive,
pseudo-random Poisson deviates with specified mean.

    >>> p = galsim.PoissonDeviate()
    >>> p()
    1
    >>> p()
    2

Methods
-------
To add deviates to every element of an image, use the syntax image.addNoise(p).

To get and set the deviate parameter, see the docstrings for the .getMean(), .setMean() method of 
each instance.
"""

_galsim.PoissonDeviate.applyTo.__func__.__doc__ = """
Add Poisson deviates to every element in a supplied Image.

Calling
-------

    >>> galsim.PoissonDeviate.applyTo(image)

On output each element of the input Image will have a pseudo-random PoissonDeviate return value 
added to it, with current mean, and then that mean subtracted.  So the average  effect on each 
pixel is zero, but there will be Poisson noise added to the image with the right variance.

To add deviates to every element of an image, the syntax image.addNoise() is preferred.
"""

_galsim.PoissonDeviate.__call__.__func__.__doc__ = """
Draw a new random number from the distribution.

Returns a Poisson deviate with current mean.
"""
_galsim.PoissonDeviate.getMean.__func__.__doc__ = "Get current distribution mean."
_galsim.PoissonDeviate.setMean.__func__.__doc__ = "Set current distribution mean."


# CCDNoise deviate docstrings
_galsim.CCDNoise.__doc__ = """
Pseudo-random number generator with a basic CCD noise model.

A CCDNoise instance is initialized given a gain level in Electrons per ADU used for the Poisson
noise term, and a Gaussian read noise in electrons (if gain > 0.) or ADU (if gain <= 0.).  With 
these parameters set, the CCDNoise operates on an Image, adding noise to each pixel following this 
model. 

Note that galsim.CCDNoise assumes the image it is applying the Poisson noise to has the sky level
included, hence generating the appropriate image noise.  The user is responsible for the 
addition of the sky level so that galsim.CCDNoise can add the proper sky noise, as well as sky
subtraction after the noise has been added.

Initialization
--------------

    >>> ccd_noise = galsim.CCDNoise(gain=1., read_noise=0.)         # Initializes ccd_noise to be a
                                                                    # CCDNoise instance using the
                                                                    # current time for the seed.

    >>> ccd_noise = galsim.CCDNoise(lseed, gain=1., read_noise=0.)  # Initializes ccd_noise to be a
                                                                    # CCDNoise instance using the
                                                                    # specified seed, where lseed is
                                                                    # a long int.

    >>> ccd_noise = galsim.CCDNoise(dev, gain=1., read_noise=0.)    # Initializes ccd_noise to share
                                                                    # the same underlying random
                                                                    # number generator as dev.

Parameters:

    gain        the gain for each pixel in electrons per ADU; setting gain <=0 will shut off the
                Poisson noise, and the Gaussian rms will take the value read_noise as being in units
                of ADU rather than electrons [default `gain = 1.`].
    read_noise  the read noise on each pixel in electrons (gain > 0.) or ADU (gain <= 0.)
                setting read_noise=0. will shut off the Gaussian noise [default `read_noise = 0.`].

Methods
-------
To add deviates to every element of an image, use the syntax image.addNoise(ccd_noise).

To get and set the deviate parameters, see the docstrings for the .getGain(), .setGain(), 
.getReadNoise() and .setReadNoise() methods of each instance.
"""

_galsim.CCDNoise.applyTo.__func__.__doc__ = """
Add noise to an input Image.

Calling
-------

    >>> galsim.CCDNoise.applyTo(image)

On output the Image instance image will have been given an additional stochastic noise according to 
the gain and read noise settings of the CCDNoise instance.

To add deviates to every element of an image, the syntax image.addNoise() is preferred.
"""
_galsim.CCDNoise.getGain.__func__.__doc__ = "Get gain in current noise model."
_galsim.CCDNoise.setGain.__func__.__doc__ = "Set gain in current noise model."
_galsim.CCDNoise.getReadNoise.__func__.__doc__ = "Get read noise in current noise model."
_galsim.CCDNoise.setReadNoise.__func__.__doc__ = "Set read noise in current noise model."


# WeibullDeviate docstrings
_galsim.WeibullDeviate.__doc__ = """
Pseudo-random Weibull-distributed deviate for shape parameter a & scale parameter b.

The Weibull distribution is related to a number of other probability distributions;  in particular,
it interpolates between the exponential distribution (a=1) and the Rayleigh distribution (a=2). 
See http://en.wikipedia.org/wiki/Weibull_distribution (a=k and b=lambda in the notation adopted in 
the Wikipedia article) for more details.  The Weibull distribution is real valued and produces 
deviates >= 0.

Initialization
--------------

    >>> w = galsim.WeibullDeviate(a=1., b=1.)         # Initializes w to be a WeibullDeviate
                                                      # instance using the current time for the seed.

    >>> w = galsim.WeibullDeviate(lseed, a=1., b=1.)  # Initializes w using the specified seed,
                                                      # where lseed is a long int.

    >>> w = galsim.WeibullDeviate(dev, a=1., b=1.)    # Initializes w to share the same underlying
                                                      # random number generator as dev.

Parameters:

    a        shape parameter of the distribution [default `a = 1`].  Must be > 0.
    b        scale parameter of the distribution [default `b = 1`].  Must be > 0.

Calling
-------
Taking the instance from the above examples, successive calls to w() then generate pseudo-random 
numbers Weibull-distributed with shape and scale parameters a and b.

    >>> w = galsim.WeibullDeviate()
    >>> w()
    2.152873075208731
    >>> w()
    2.0826856212853846

Methods
-------
To add deviates to every element of an image, use the syntax image.addNoise(w).

To get and set the deviate parameters, see the docstrings for the .getA(), .setA(), .getB() and 
.setB() methods of each instance.
"""

_galsim.WeibullDeviate.applyTo.__func__.__doc__ = """
Add Weibull-distributed deviates to every element in a supplied Image.

Calling
-------

    >>> galsim.WeibullDeviate.applyTo(image)

On output each element of the input Image will have a pseudo-random WeibullDeviate return value 
added to it, with current values of a and b.

To add deviates to every element of an image, the syntax image.addNoise() is preferred.
"""

_galsim.WeibullDeviate.__call__.__func__.__doc__ = """
Draw a new random number from the distribution.

Returns a Weibull-distributed deviate with current a and b.
"""
_galsim.WeibullDeviate.getA.__func__.__doc__ = "Get current distribution shape parameter a."
_galsim.WeibullDeviate.setA.__func__.__doc__ = "Set current distribution shape parameter a."
_galsim.WeibullDeviate.getB.__func__.__doc__ = "Get current distribution shape parameter b."
_galsim.WeibullDeviate.setB.__func__.__doc__ = "Set current distribution shape parameter b."


# GammaDeviate docstrings
_galsim.GammaDeviate.__doc__ = """
Pseudo-random Gamma-distributed deviate for parameters alpha & beta.

See http://en.wikipedia.org/wiki/Gamma_distribution (note that alpha=k and beta=theta in the
notation adopted in the Boost.Random routine called by this class).  The Gamma distribution is a 
real-valued distribution producing deviates >= 0.

Initialization
--------------

    >>> gam = galsim.GammaDeviate(alpha=1., beta=1.)         # Initializes gam to be a GammaDeviate
                                                             # instance using the current time for
                                                             # the seed.

    >>> gam = galsim.GammaDeviate(lseed, alpha=1., beta=1.)  # Initializes gam using the specified
                                                             # seed, where lseed is a long int.

    >>> gam = galsim.GammaDeviate(dev alpha=1., beta=1.)     # Initializes gam to share the same
                                                             # underlying random number generator as
                                                             # dev.

Parameters:

    alpha    shape parameter of the distribution [default `alpha = 1`].  Must be > 0.
    beta     scale parameter of the distribution [default `beta = 1`].  Must be > 0.

Calling
-------
Taking the instance from the above examples, successive calls to g() will return successive, 
pseudo-random Gamma-distributed deviates with shape and scale parameters alpha and beta. 

    >>> gam = galsim.GammaDeviate()
    >>> gam()
    0.020092014608829315
    >>> gam()
    0.5062533114685395

Methods
-------
To add deviates to every element of an image, use the syntax image.addNoise(gam).

To get and set the deviate parameters, see the docstrings for the .getAlpha(), .setAlpha(), 
.getBeta() and .setBeta() methods of each instance.

To add deviates to every element of an image, the syntax image.addNoise() is preferred.
"""

_galsim.GammaDeviate.applyTo.__func__.__doc__ = """
Add Gamma-distributed deviates to every element in a supplied Image.

Calling
-------

    >>> galsim.GammaDeviate.applyTo(image)

On output each element of the input Image will have a pseudo-random GammaDeviate return value added
to it, with current values of alpha and beta.
"""

_galsim.GammaDeviate.__call__.__func__.__doc__ = """
Draw a new random number from the distribution.

Returns a Gamma-distributed deviate with current alpha and beta.
"""
_galsim.GammaDeviate.getAlpha.__func__.__doc__ = "Get current distribution shape parameter alpha."
_galsim.GammaDeviate.setAlpha.__func__.__doc__ = "Set current distribution shape parameter alpha."
_galsim.GammaDeviate.getBeta.__func__.__doc__ = "Get current distribution shape parameter beta."
_galsim.GammaDeviate.setBeta.__func__.__doc__ = "Set current distribution shape parameter beta."


# Chi2Deviate docstrings
_galsim.Chi2Deviate.__doc__ = """
Pseudo-random Chi^2-distributed deviate for degrees-of-freedom parameter n.

See http://en.wikipedia.org/wiki/Chi-squared_distribution (note that k=n in the notation adopted in
the Boost.Random routine called by this class).  The Chi^2 distribution is a real-valued 
distribution producing deviates >= 0.

Initialization
--------------

    >>> chis = galsim.Chi2Deviate(n=1.)          # Initializes chis to be a Chi2Deviate instance
                                                 # using the current time for the seed.

    >>> chis = galsim.Chi2Deviate(lseed, n=1.)   # Initializes chis using the specified seed, where
                                                 # lseed is a long int.

    >>> chis = galsim.Chi2Deviate(dev, n=1.)     # Initializes chis to share the same underlying
                                                 # random number generator as dev.

Parameters:
    n   number of degrees of freedom for the output distribution [default `n = 1`].  Must be > 0.

Calling
-------
Taking the instance from the above examples, successive calls to g() will return successive, 
pseudo-random Chi^2-distributed deviates with degrees-of-freedom parameter n.

    >>> chis = galsim.Chi2Deviate()
    >>> chis()
    0.35617890086874854
    >>> chis()
    0.17269982670901735

Methods
-------
To add deviates to every element of an image, use the syntax image.addNoise(chis).

To get and set the deviate parameter, see the docstrings for the .getN(), .setN() methods of each
instance.
"""

_galsim.Chi2Deviate.applyTo.__func__.__doc__ = """
Add Chi^2-distributed deviates to every element in a supplied Image.

Calling
-------

    >>> galsim.Chi2Deviate.applyTo(image)

On output each element of the input Image will have a pseudo-random Chi2Deviate return value added 
to it, with current degrees-of-freedom parameter n.

To add deviates to every element of an image, the syntax image.addNoise() is preferred.
"""

_galsim.Chi2Deviate.__call__.__func__.__doc__ = """
Draw a new random number from the distribution.

Returns a Chi2-distributed deviate with current n degrees of freedom.
"""
_galsim.Chi2Deviate.getN.__func__.__doc__ = "Get current distribution n degrees of freedom."
_galsim.Chi2Deviate.setN.__func__.__doc__ = "Set current distribution n degrees of freedom."

