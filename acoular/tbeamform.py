# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2017, Acoular Development Team.
#------------------------------------------------------------------------------
"""Implements beamformers in the time domain.

.. autosummary::
    :toctree: generated/

    BeamformerTime
    BeamformerTimeTraj
    BeamformerTimeSq
    BeamformerTimeSqTraj
    IntegratorSectorTime
"""

# imports from other packages
from __future__ import print_function, division
from six import next
from numpy import array, newaxis, empty, sqrt, arange, clip, r_, zeros, \
histogram, unique, cross, dot, where, s_ , sum
from traits.api import Float, CArray, Property, Trait, Bool, Delegate, \
cached_property, List, Instance
from traitsui.api import View, Item
from traitsui.menu import OKCancelButtons
from traits.trait_errors import TraitError

# acoular imports
from .internal import digest
from .grids import RectGrid
from .trajectory import Trajectory
from .tprocess import TimeInOut
from .fbeamform import SteeringVector


def const_power_weight( bf ):
    """
    Internal helper function for :class:`BeamformerTime`
    
    Provides microphone weighting 
    to make the power per unit area of the
    microphone array geometry constant.
    
    Parameters
    ----------
    bf: :class:`BeamformerTime` object
        
          
    Returns
    -------
    array of floats
        The weight factors.
    """

    r = bf.steer.env._r(zeros((3, 1)), bf.steer.mics.mpos) # distances to center
    # round the relative distances to one decimal place
    r = (r/r.max()).round(decimals=1)
    ru, ind = unique(r, return_inverse=True)
    ru = (ru[1:]+ru[:-1])/2
    count, bins = histogram(r, r_[0, ru, 1.5*r.max()-0.5*ru[-1]])
    bins *= bins
    weights = sqrt((bins[1:]-bins[:-1])/count)
    weights /= weights.mean()
    return weights[ind]

# possible choices for spatial weights
possible_weights = {'none':None, 
                    'power':const_power_weight}


class BeamformerTime( TimeInOut ):
    """
    Provides a basic time domain beamformer with time signal output
    for a spatially fixed grid.
    """


    # Instance of :class:`~acoular.fbeamform.SteeringVector` or its derived classes
    # that contains information about the steering vector. This is a private trait.
    # Do not set this directly, use `steer` trait instead.
    _steer_obj = Instance(SteeringVector(), SteeringVector)   
    
    #: :class:`~acoular.fbeamform.SteeringVector` or derived object. 
    #: Defaults to :class:`~acoular.fbeamform.SteeringVector` object.
    steer = Property(desc="steering vector object")  
    
    def _get_steer(self):
        return self._steer_obj
    
    def _set_steer(self, steer):
        if type(steer) == SteeringVector:
            # This condition may be replaced at a later time by: isinstance(steer, SteeringVector): -- (derived classes allowed)
            self._steer_obj = steer
        elif steer in ('true level', 'true location', 'classic', 'inverse'):
            # Type of steering vectors, see also :ref:`Sarradj, 2012<Sarradj2012>`.
            print("Warning! Deprecated use of 'steer' trait. Better use object of class 'SteeringVector'")
            self._steer_obj = SteeringVector(steer_type = steer)
        else:
            raise(TraitError(args=self,
                             name='steer', 
                             info='SteeringVector',
                             value=steer))

    # --- List of backwards compatibility traits and their setters/getters -----------
    
    # :class:`~acoular.environments.Environment` or derived object. 
    # Deprecated! Only kept for backwards compatibility. 
    # Now governed by :attr:`steer` trait.
    env = Property()
    
    def _get_env(self):
        return self._steer_obj.env    
    
    def _set_env(self, env):
        print("Warning! Deprecated use of 'env' trait.")
        self._steer_obj.env = env
    
    # The speed of sound.
    # Deprecated! Only kept for backwards compatibility. 
    # Now governed by :attr:`steer` trait.
    c = Property()
    
    def _get_c(self):
        return self._steer_obj.env.c
    
    def _set_c(self, c):
        print("Warning! Deprecated use of 'c' trait.")
        self._steer_obj.env.c = c
   
    # :class:`~acoular.grids.Grid`-derived object that provides the grid locations.
    # Deprecated! Only kept for backwards compatibility. 
    # Now governed by :attr:`steer` trait.
    grid = Property()

    def _get_grid(self):
        return self._steer_obj.grid
    
    def _set_grid(self, grid):
        print("Warning! Deprecated use of 'grid' trait.")
        self._steer_obj.grid = grid
    
    # :class:`~acoular.microphones.MicGeom` object that provides the microphone locations.
    # Deprecated! Only kept for backwards compatibility. 
    # Now governed by :attr:`steer` trait
    mpos = Property()
    
    def _get_mpos(self):
        return self._steer_obj.mics
    
    def _set_mpos(self, mpos):
        print("Warning! Deprecated use of 'mpos' trait.")
        self._steer_obj.mics = mpos
    
    
    # Sound travel distances from microphone array center to grid points (r0)
    # and all array mics to grid points (rm). Readonly.
    # Deprecated! Only kept for backwards compatibility. 
    # Now governed by :attr:`steer` trait
    r0 = Property()
    def _get_r0(self):
        return self._steer_obj.r0
    
    rm = Property()
    def _get_rm(self):
        return self._steer_obj.rm
    
    # --- End of backwards compatibility traits --------------------------------------

    #: Number of channels in output (=number of grid points).
    numchannels = Delegate('grid', 'size')

    #: Spatial weighting function.
    weights = Trait('none', possible_weights, 
        desc="spatial weighting function")
    # (from timedomain.possible_weights)
    
    # internal identifier
    digest = Property( 
        depends_on = ['steer.digest', 'source.digest', 'weights', '__class__'], 
        )

    traits_view = View(
        [
            [Item('steer{}', style='custom')], 
            [Item('source{}', style='custom'), '-<>'], 
            [Item('weights{}', style='simple')], 
            '|'
        ], 
        title='Beamformer options', 
        buttons = OKCancelButtons
        )

    @cached_property
    def _get_digest( self ):
        return digest(self)
    
         
    def result( self, num=2048 ):
        """
        Python generator that yields the beamformer output block-wise.
        
        Parameters
        ----------
        num : integer, defaults to 2048
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block).
        
        Returns
        -------
        Samples in blocks of shape (num, :attr:`numchannels`). 
            :attr:`numchannels` is usually very large.
            The last block may be shorter than num.
        """
        if self.weights_:
            w = self.weights_(self)[newaxis]
        else:
            w = 1.0
        c = self.c/self.sample_freq
        delays = self.rm/c
        d_index = array(delays, dtype=int) # integer index
        d_interp1 = delays % 1 # 1st coeff for lin interpolation between samples
        d_interp2 = 1-d_interp1 # 2nd coeff for lin interpolation 
        d_index2 = arange(self.steer.mics.num_mics)
#        amp = (self.rm/self.r0[:, newaxis]) # multiplication factor
        amp = (w/(self.rm*self.rm)).sum(1) * self.r0
        amp = 1.0/(amp[:, newaxis]*self.rm) # multiplication factor
        d_interp1 *= amp # premultiplication, to save later ops
        d_interp2 *= amp
        dmin = d_index.min() # minimum index
        dmax = d_index.max()+1 # maximum index
        aoff = dmax-dmin # index span
        #working copy of data:
        zi = empty((aoff+num, self.source.numchannels), dtype=float) 
        o = empty((num, self.grid.size), dtype=float) # output array
        offset = aoff # start offset for working array
        ooffset = 0 # offset for output array
        for block in self.source.result(num):
            ns = block.shape[0] # numbers of samples and channels
            maxoffset = ns-dmin # ns - aoff +aoff -dmin
            zi[aoff:aoff+ns] = block * w # copy data to working array
            # loop over data samples 
            while offset < maxoffset:
                # yield output array if full
                if ooffset == num:
                    yield o
                    ooffset = 0
                # the next line needs to be implemented faster
                o[ooffset] = (zi[offset+d_index, d_index2]*d_interp1 + \
                        zi[offset+d_index+1, d_index2]*d_interp2).sum(-1)
                offset += 1
                ooffset += 1
            # copy remaining samples in front of next block
            zi[0:aoff] = zi[-aoff:]
            offset -= num
        # remaining data chunk 
        yield o[:ooffset]
            

class BeamformerTimeSq( BeamformerTime ):
    """
    Provides a time domain beamformer with time-dependend
    power signal output and possible autopower removal
    for a spatially fixed grid.
    """
    
    #: Boolean flag, if 'True' (default), the main diagonal is removed before beamforming.
    r_diag = Bool(True, 
        desc="removal of diagonal")

    # internal identifier
    digest = Property( 
        depends_on = ['steer.digest', 'source.digest', 'r_diag', \
                      'weights', '__class__'], 
        )

    traits_view = View(
        [
            [Item('steer{}', style='custom')], 
            [Item('source{}', style='custom'), '-<>'], 
            [Item('r_diag', label='diagonal removed')], 
            [Item('weights{}', style='simple')], 
            '|'
        ], 
        title='Beamformer options', 
        buttons = OKCancelButtons
        )


    @cached_property
    def _get_digest( self ):
        return digest(self)
        
    # generator, delivers the beamformer result
    def result( self, num=2048 ):
        """
        Python generator that yields the *squared* beamformer 
        output with optional removal of autocorrelation block-wise.
        
        Parameters
        ----------
        num : integer, defaults to 2048
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block) .
        
        Returns
        -------
        Samples in blocks of shape \
        (num, :attr:`~BeamformerTime.numchannels`). 
            :attr:`~BeamformerTime.numchannels` is usually very 
            large (number of grid points).
            The last block may be shorter than num.
        """

        if self.weights_:
            w = self.weights_(self)[newaxis]
        else:
            w = 1.0
        c = self.c/self.source.sample_freq
        delays = self.rm/c
        d_index = array(delays, dtype=int) # integer index
        d_interp1 = delays % 1 # 1st coeff for lin interpolation between samples
        d_interp2 = 1-d_interp1 # 2nd coeff for lin interpolation 
        d_index2 = arange(self.steer.mics.num_mics)
#        amp = (self.rm/self.r0[:, newaxis]) # multiplication factor
        amp = (w/(self.rm*self.rm)).sum(1) * self.r0
        amp = 1.0/(amp[:, newaxis]*self.rm) # multiplication factor
        d_interp1 *= amp # premultiplication, to save later ops
        d_interp2 *= amp
        dmin = d_index.min() # minimum index
        dmax = d_index.max()+1 # maximum index
#        print dmin, dmax
        aoff = dmax-dmin # index span
        #working copy of data:
        zi = empty((aoff+num, self.source.numchannels), dtype=float)
        o = empty((num, self.grid.size), dtype=float) # output array
        temp = empty((self.grid.size, self.source.numchannels), dtype=float)
        offset = aoff # start offset for working array
        ooffset = 0 # offset for output array
        for block in self.source.result(num):
            ns = block.shape[0] # numbers of samples and channels
            maxoffset = ns-dmin # ns - aoff +aoff -dmin
            zi[aoff:aoff+ns] = block * w # copy data to working array
            # loop over data samples 
            while offset < maxoffset:
                # yield output array if full
                if ooffset == num:
                    yield o
                    ooffset = 0
                # the next line needs to be implemented faster
                temp[:, :] = (zi[offset+d_index, d_index2]*d_interp1 \
                    + zi[offset+d_index+1, d_index2]*d_interp2)
                if self.r_diag:
                    # simple sum and remove autopower
                    o[ooffset] = clip(temp.sum(-1)**2 - \
                            (temp**2).sum(-1), 1e-100, 1e+100)
                else:
                    # simple sum
                    o[ooffset] = temp.sum(-1)**2
                offset += 1
                ooffset += 1
            # copy remaining samples in front of next block
            zi[0:aoff] = zi[-aoff:]
            offset -= num
        # remaining data chunk 
        yield o[:ooffset]




class BeamformerTimeTraj( BeamformerTime ):
    """
    Provides a basic time domain beamformer with time signal output
    for a grid moving along a trajectory.
    """


    #: :class:`~acoular.trajectory.Trajectory` or derived object.
    #: Start time is assumed to be the same as for the samples.
    trajectory = Trait(Trajectory, 
        desc="trajectory of the grid center")

    #: Reference vector, perpendicular to the y-axis of moving grid.
    rvec = CArray( dtype=float, shape=(3, ), value=array((0, 0, 0)), 
        desc="reference vector")
    
    # internal identifier
    digest = Property( 
        depends_on = ['steer.digest', 'source.digest', 'weights',  \
                      'rvec', 'trajectory.digest', '__class__'], 
        )

    traits_view = View(
        [
            [Item('steer{}', style='custom')], 
            [Item('source{}', style='custom'), '-<>'], 
            [Item('trajectory{}', style='custom')],
            [Item('weights{}', style='simple')], 
            '|'
        ], 
        title='Beamformer options', 
        buttons = OKCancelButtons
        )


    @cached_property
    def _get_digest( self ):
        return digest(self)
        
    def result( self, num=2048 ):
        """
        Python generator that yields the beamformer 
        output block-wise. 
        
        Optional removal of autocorrelation.
        The "moving" grid can be translated and optionally rotated.
        
        Parameters
        ----------
        num : integer, defaults to 2048
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block).
        
        Returns
        -------
        Samples in blocks of shape  \
        (num, :attr:`~BeamformerTime.numchannels`). 
            :attr:`~BeamformerTime.numchannels` is usually very \
            large (number of grid points).
            The last block may be shorter than num. \
            The output starts for signals that were emitted 
            from the grid at `t=0`.
        """

        if self.weights_:
            w = self.weights_(self)[newaxis]
        else:
            w = 1.0
        c = self.steer.env.c/self.source.sample_freq
        # temp array for the grid co-ordinates
        gpos = self.grid.pos()
        # max delay span = sum of
        # max diagonal lengths of circumscribing cuboids for grid and micarray
        dmax = sqrt(((gpos.max(1)-gpos.min(1))**2).sum())
        dmax += sqrt(((self.steer.mics.mpos.max(1)-self.steer.mics.mpos.min(1))**2).sum())
        dmax = int(dmax/c)+1 # max index span
        zi = empty((dmax+num, self.source.numchannels), \
            dtype=float) #working copy of data
        o = empty((num, self.grid.size), dtype=float) # output array
        temp = empty((self.grid.size, self.source.numchannels), dtype=float)
        d_index2 = arange(self.steer.mics.num_mics, dtype=int) # second index (static)
        offset = dmax+num # start offset for working array
        ooffset = 0 # offset for output array      
        # generators for trajectory, starting at time zero
        start_t = 0.0
        g = self.trajectory.traj( start_t, delta_t=1/self.source.sample_freq)
        g1 = self.trajectory.traj( start_t, delta_t=1/self.source.sample_freq, 
                                  der=1)
                                  
        rflag = (self.rvec == 0).all() #flag translation vs. rotation
        data = self.source.result(num)
        flag = True
        while flag:
            # yield output array if full
            if ooffset == num:
                yield o
                ooffset = 0
            if rflag:
                # grid is only translated, not rotated
                tpos = gpos + array(next(g))[:, newaxis]
            else:
                # grid is both translated and rotated
                loc = array(next(g)) #translation array([0., 0.4, 1.])
                dx = array(next(g1)) #direction vector (new x-axis)
                dy = cross(self.rvec, dx) # new y-axis
                dz = cross(dx, dy) # new z-axis
                RM = array((dx, dy, dz)).T # rotation matrix
                RM /= sqrt((RM*RM).sum(0)) # column normalized
                tpos = dot(RM, gpos)+loc[:, newaxis] # rotation+translation
            rm = self.steer.env._r( tpos, self.steer.mics.mpos)
            r0 = self.steer.env._r( tpos)
            delays = rm/c
            d_index = array(delays, dtype=int) # integer index
            d_interp1 = delays % 1 # 1st coeff for lin interpolation
            d_interp2 = 1-d_interp1 # 2nd coeff for lin interpolation
            amp = (w/(rm*rm)).sum(1) * r0
            amp = 1.0/(amp[:, newaxis]*rm) # multiplication factor
            # now, we have to make sure that the needed data is available                 
            while offset+d_index.max()+2>dmax+num:
                # copy remaining samples in front of next block
                zi[0:dmax] = zi[-dmax:]
                # the offset is adjusted by one block length
                offset -= num
                # test if data generator is exhausted
                try:
                    # get next data
                    block = next(data)
                except StopIteration:
                    print(loc)
                    flag = False
                    break
                # samples in the block, equals to num except for the last block
                ns = block.shape[0]                
                zi[dmax:dmax+ns] = block * w# copy data to working array
            else:
                # the next line needs to be implemented faster
                # it eats half of the time
                temp[:, :] = (zi[offset+d_index, d_index2]*d_interp1 \
                            + zi[offset+d_index+1, d_index2]*d_interp2)*amp
                o[ooffset] = temp.sum(-1)
                offset += 1
                ooffset += 1
        # remaining data chunk
        yield o[:ooffset]

        
class BeamformerTimeSqTraj( BeamformerTimeSq ):
    """
    Provides a time domain beamformer with time-dependent
    power signal output and possible autopower removal
    for a grid moving along a trajectory.
    """
    
    #: :class:`~acoular.trajectory.Trajectory` or derived object.
    #: Start time is assumed to be the same as for the samples.
    trajectory = Trait(Trajectory, 
        desc="trajectory of the grid center")

    #: Reference vector, perpendicular to the y-axis of moving grid.
    rvec = CArray( dtype=float, shape=(3, ), value=array((0, 0, 0)), 
        desc="reference vector")
    
    # internal identifier
    digest = Property( 
        depends_on = ['steer.digest', 'source.digest', 'r_diag', 'weights', \
                      'rvec', 'trajectory.digest', '__class__'], 
        )

    traits_view = View(
        [
            [Item('steer{}', style='custom')], 
            [Item('source{}', style='custom'), '-<>'], 
            [Item('trajectory{}', style='custom')],
            [Item('r_diag', label='diagonal removed')], 
            [Item('weights{}', style='simple')], 
            '|'
        ], 
        title='Beamformer options', 
        buttons = OKCancelButtons
        )

    @cached_property
    def _get_digest( self ):
        return digest(self)
        
    def result( self, num=2048 ):
        """
        Python generator that yields the *squared* beamformer 
        output block-wise. 
        
        Optional removal of autocorrelation.
        The "moving" grid can be translated and optionally rotated.
        
        Parameters
        ----------
        num : integer, defaults to 2048
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block).
        
        Returns
        -------
        Samples in blocks of shape  \
        (num, :attr:`~BeamformerTime.numchannels`). 
            :attr:`~BeamformerTime.numchannels` is usually very \
            large (number of grid points).
            The last block may be shorter than num. \
            The output starts for signals that were emitted 
            from the grid at `t=0`.
        """

        if self.weights_:
            w = self.weights_(self)[newaxis]
        else:
            w = 1.0
        c = self.env.c/self.source.sample_freq
        # temp array for the grid co-ordinates
        gpos = self.grid.pos()
        # max delay span = sum of
        # max diagonal lengths of circumscribing cuboids for grid and micarray
        dmax = sqrt(((gpos.max(1)-gpos.min(1))**2).sum())
        dmax += sqrt(((self.steer.mics.mpos.max(1)-self.steer.mics.mpos.min(1))**2).sum())
        dmax = int(dmax/c)+1 # max index span
        zi = empty((dmax+num, self.source.numchannels), \
            dtype=float) #working copy of data
        o = empty((num, self.grid.size), dtype=float) # output array
        temp = empty((self.grid.size, self.source.numchannels), dtype=float)
        d_index2 = arange(self.steer.mics.num_mics, dtype=int) # second index (static)
        offset = dmax+num # start offset for working array
        ooffset = 0 # offset for output array      
        # generators for trajectory, starting at time zero
        start_t = 0.0
        g = self.trajectory.traj( start_t, delta_t=1/self.source.sample_freq)
        g1 = self.trajectory.traj( start_t, delta_t=1/self.source.sample_freq, 
                                  der=1)
        rflag = (self.rvec == 0).all() #flag translation vs. rotation
        data = self.source.result(num)
        flag = True
        while flag:
            # yield output array if full
            if ooffset == num:
                yield o
                ooffset = 0
            if rflag:
                # grid is only translated, not rotated
                tpos = gpos + array(next(g))[:, newaxis]
            else:
                # grid is both translated and rotated
                loc = array(next(g)) #translation
                dx = array(next(g1)) #direction vector (new x-axis)
                dy = cross(self.rvec, dx) # new y-axis
                dz = cross(dx, dy) # new z-axis
                RM = array((dx, dy, dz)).T # rotation matrix
                RM /= sqrt((RM*RM).sum(0)) # column normalized
                tpos = dot(RM, gpos)+loc[:, newaxis] # rotation+translation
            rm = self.steer.env._r( tpos, self.steer.mics.mpos)
            r0 = self.steer.env._r( tpos)
            delays = rm/c
            d_index = array(delays, dtype=int) # integer index
            d_interp1 = delays % 1 # 1st coeff for lin interpolation
            d_interp2 = 1-d_interp1 # 2nd coeff for lin interpolation
            amp = (w/(rm*rm)).sum(1) * r0
            amp = 1.0/(amp[:, newaxis]*rm) # multiplication factor
            # now, we have to make sure that the needed data is available                 
            while offset+d_index.max()+2>dmax+num:
                # copy remaining samples in front of next block
                zi[0:dmax] = zi[-dmax:]
                # the offset is adjusted by one block length
                offset -= num
                # test if data generator is exhausted
                try:
                    # get next data
                    block = next(data)
                except StopIteration:
                    flag = False
                    break
                # samples in the block, equals to num except for the last block
                ns = block.shape[0]                
                zi[dmax:dmax+ns] = block * w# copy data to working array
            else:
                # the next line needs to be implemented faster
                # it eats half of the time
                temp[:, :] = (zi[offset+d_index, d_index2]*d_interp1 \
                            + zi[offset+d_index+1, d_index2]*d_interp2)*amp
                if self.r_diag:
                    # simple sum and remove autopower
                    o[ooffset] = clip(temp.sum(-1)**2 - \
                        (temp**2).sum(-1), 1e-100, 1e+100)
                else:
                    # simple sum
                    o[ooffset] = temp.sum(-1)**2
                offset += 1
                ooffset += 1
        # remaining data chunk
        yield o[:ooffset]
                       

class IntegratorSectorTime( TimeInOut ):
    """
    Provides an Integrator in the time domain.
    """

    #: :class:`~acoular.grids.RectGrid` object that provides the grid locations.
    grid = Trait(RectGrid, 
        desc="beamforming grid")
        
    #: List of sectors in grid
    sectors = List()

    #: Clipping, in Dezibel relative to maximum (negative values)
    clip = Float(-350.0)

    #: Number of channels in output (= number of sectors).
    numchannels = Property( depends_on = ['sectors', ])

    # internal identifier
    digest = Property( 
        depends_on = ['sectors', 'clip', 'grid.digest', 'source.digest', \
        '__class__'], 
        )

    traits_view = View(
        [
            [Item('sectors', style='custom')], 
            [Item('grid', style='custom'), '-<>'], 
            '|'
        ], 
        title='Integrator', 
        buttons = OKCancelButtons
        )

    @cached_property
    def _get_digest( self ):
        return digest(self)
        
    @cached_property
    def _get_numchannels ( self ):
        return len(self.sectors)

    def result( self, num=1 ):
        """
        Python generator that yields the source output integrated over the given 
        sectors, block-wise.
        
        Parameters
        ----------
        num : integer, defaults to 1
            This parameter defines the size of the blocks to be yielded
            (i.e. the number of samples per block).
        
        Returns
        -------
        Samples in blocks of shape (num, :attr:`numchannels`). 
        :attr:`numchannels` is the number of sectors.
        The last block may be shorter than num.
        """
        inds = [self.grid.indices(*sector) for sector in self.sectors]
        gshape = self.grid.shape
        o = empty((num, self.numchannels), dtype=float) # output array
        for r in self.source.result(num):
            ns = r.shape[0]
            mapshape = (ns,) + gshape
            rmax = r.max()
            rmin = rmax * 10**(self.clip/10.0)
            r = where(r>rmin, r, 0.0)
            i = 0
            for ind in inds:
                h = r[:].reshape(mapshape)[ (s_[:],) + ind ]
                o[:ns, i] = h.reshape(h.shape[0], -1).sum(axis=1)
                i += 1
            yield o[:ns]


