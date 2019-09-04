# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------
"""
Implements class for configuring acoular.

.. autosummary::
    :toctree: generated/

    Config
"""

from traits.api import Trait,Property, HasStrictTraits

class Config(HasStrictTraits):
    """
    This class implements the global configuration of the acoular package.

    An instance of this class can be accessed for adjustment of the following 
    properties.
    General caching behaviour can be controlled by :attr:`global_caching`.
    The package used to read and write .h5 files can be specified 
    by :attr:`h5library`.    
    
    Example: 
        For using acoular with h5py package and overwrite existing cache:
        
        import acoular
        acoular.config.h5library = "h5py"
        acoular.config.global_caching = "overwrite"
    """
    
    def __init__(self):
        HasStrictTraits.__init__(self)
        self._assert_h5library()
    
    #: Flag that globally defines caching behaviour of acoular classes
    #: defaults to 'individual'.
    #:
    #: * 'individual': Acoular classes handle caching behavior individually.
    #: * 'all': Acoular classes cache everything and read from cache if possible.
    #: * 'none': Acoular classes do not cache results. Cachefiles are not created.
    #: * 'readonly': Acoular classes do not actively cache, but read from cache if existing.
    #: * 'overwrite': Acoular classes replace existing cachefile content with new data.
    global_caching = Property()
    
    _global_caching = Trait('individual','all','none','readonly','overwrite') 

    #: Flag that globally defines package used to read and write .h5 files 
    #: defaults to 'pytables'. If 'pytables' can not be imported, 'h5py' is used
    h5library = Property()
    
    _h5library = Trait('pytables','h5py')
    
    def _get_global_caching(self):
        return self._global_caching

    def _set_global_caching(self,globalCachingValue):
        self._global_caching = globalCachingValue
        
    def _get_h5library(self):
        return self._h5library
    
    def _set_h5library(self,libraryName):
        self._h5library = libraryName 
        
    def _assert_h5library(self):
        try:
            import tables  
            self.h5library = 'pytables'
        except:
            try:
                import h5py
                self.h5library = 'h5py'
            except:
                raise ImportError("packages h5py and pytables are missing!")
            
config = Config()
        
