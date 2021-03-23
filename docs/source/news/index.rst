What's new
============

20.10
------------
	
	* Supports Python 3.6, 3.7, 3.8
	* New base classes for time signal processing: :class:`~acoular.tprocess.Filter`, :class:`~acoular.tprocess.FilterBank`
		* New filter classes: :class:`~acoular.tprocess.TimeExpAverage`, :class:`~acoular.tprocess.FiltFreqWeight`, :class:`~acoular.tprocess.OctaveFilterBank`
		* Demo script is now part of module (see :doc:`../get_started/index` for usage)
	* New class for processing sound card input: :class:`~acoular.sdinput.SoundDeviceSamplesGenerator`
	* New class for cumulative averaging: :class:`~acoular.tprocess.TimeCumAverage`
	* New grid classes :class:`~acoular.grids.ImportGrid`, :class:`~acoular.grids.LineGrid`, :class:`~acoular.grids.MergeGrid`
	* New versatile integration sector classes :class:`~acoular.grids.RectSector`, :class:`~acoular.grids.CircSector`, :class:`~acoular.grids.PolySector`, :class:`~acoular.grids.ConvexSector`, :class:`~acoular.grids.MultiSector`
	* New class for mixing multiple channels :class:`~acoular.tprocess.ChannelMixer`
	* New class for using arbitrary sources as signal: :class:`~acoular.signals.GenericSignalGenerator`
	* New time-domain beamforming classes for CLEAN-T method: :class:`~acoular.tbeamform.BeamformerCleant`, :class:`~acoular.tbeamform.BeamformerCleantSq`, :class:`~acoular.tbeamform.BeamformerCleantTraj`, :class:`~acoular.tbeamform.BeamformerCleantSqTraj`
	* Adds possibility to store/load metadata to/from HDF files with :class:`~acoular.tprocess.WriteH5`/:class:`~acoular.sources.TimeSamples` classes
	* New submodule :mod:`~acoular.tools` containing several helper functions, e.g. for data aggregation
	* :class:`~acoular.tprocess.WriteWAV`: user can optionally set name of output wav file
	* Bugfix: PowerSpectra.freq_range / .ind_low / .ind_high are now correctly updated depending on changed attributes
	* Bugfix: :class:`~acoular.signals.SineGenerator` amplitude is now set via :attr:`~acoular.signals.SineGenerator.amplitude` attribute
	* Some minor fixes


20.02
------------
	
	* Adds gradient-based solver for BeamformerCMF (L_BFGS_B)
	* Adds possibilty to take into account convective amplification of moving sources in BeamformerTimeTraj
	* TraitsUI support of the classes has to be activated via :attr:`~acoular.configuration.config` 
    * Bugfix: use left-orientated coordinate system in rotating flow environment
    * Bugfix: correct wrong angle shift in spline interpolation
    * Removes several Python 2.7-specific implementations


19.11
------------
    * Adds new classes for handling rotating data, including detection of trigger signals and interpolation of sensor data for virtual array emulation (:class:`~acoular.tprocess.Trigger`, :class:`~acoular.tprocess.AngleTracker`, :class:`~acoular.tprocess.SpatialInterpolator`, :class:`~acoular.tprocess.SpatialInterpolatorRotation`, :class:`~acoular.tprocess.SpatialInterpolatorConstantRotation`)
    * Introduces new :class:`~acoular.tprocess.SampleSplitter` class, which allows distribution of data streams 
    * Adds new (global) caching options for more flexible cache file handling (e.g. never cache results, always cache, cache read-only). See :class:`~acoular.configuration.config` for information on how to use this.
    * User can choose whether to use h5py or pytables package for handling hdf files. See :class:`~acoular.configuration.config` for information on how to use this.
    * Change: BeamformerGIB behaviour (not calculating sources with eigenvalue of zero)
    * Bugfix: BeamformerTime interpolation
    * Bugfix: Integer division in PNoiseGenerator
    * Test suite and CI updates


19.08
------------
    
    * Supports Python 3.5, 3.6, 3.7
    * This will be the last version to officially support Python 2.7
    * Cache and data directories are now always created in current directory (Linux and Windows)
    * Bugfix: Steering vector backwards compatibility
    * Bugfix: Ambiguous caching (changes in an object's class name as well as changes in the data file content are now monitored for caching)
    * PowerSpectra: Frequency range to be evaluated can be set directly
    * Some code clean-up
    * Renamed examples



19.02
------------
    
    * Adds support for Python 3.7
    * Introduces new :class:`~acoular.fbeamform.SteeringVector` class (see :doc:`../get_started/index` and :doc:`../examples/index`  for usage). With this, some of the Beamformer and PointSource traits are deprecated and should no longer be used. While the current version is intended to be fully compatible with older scripts, deprecation warnings will be raised if necessary.
    * Introduces optional use of reference distance for SPL evaluation (current default: reference position at (x,y,z)=(0,0,0) )
    * Introduces some basic Unit tests to evaluate the beamformer results 
    * Bugfix: CLEAN algorithm now uses correct PSFs
    * some minor bugfixes



18.01
------------

    * Added new DAMAS solving strategies (BeamformerDamasPlus)
    * Added Generalized Inverse Beamforming
    * Floating point precision of CSM, PSF and beamformer customizable (default: float64) -- affects cache file size
    * PowerSpectra class now includes EigSpectra functionality (EigSpectra still callable for backwards compatibility)
    * Inverse methods: unit of sound pressure for internal calculation customizable (default: nPa) for better numeric stability with sklearn solvers. Still returns all values in Pa.
    * Bugfix: BeamformerFunctional works now with steering vector formulation II (inverse) and III (true level) which produced incorrect results in the past. 
    * Bugfix: BeamformerFunctional can only be called when the diagonal of the CSM is included
    * Bugfix: Corrected calculation of PSF for steering vector formulation IV
    * Bugfix: Behaviour of normalizing PSF at assumed source location (psf=1) is removed
	




17.11
------------

    * Added support for Python 3.4, 3.5 and 3.6 
    * Implementation of fast/parallelized code now with Numba (instead of C++ and SciPy.weave)
    * cross spectral matrix (CSM) orientation changed (was transposed in earlier versions). Please do not use the cache files from earlier versions in version 17.11!
    	



