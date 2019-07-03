# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611,C0111,C0103,R0901,R0902,R0903,R0904,W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2017, Acoular Development Team.
#------------------------------------------------------------------------------

# imports from other packages
from __future__ import print_function
from traits.api import HasPrivateTraits, Bool, Str
from os import path, mkdir, environ
import tables
from weakref import WeakValueDictionary
import gc

# path to cache directory
cache_dir = path.join(path.curdir,'cache')
if not path.exists(cache_dir):
    mkdir(cache_dir)

# path to working directory (used for import to *.h5 files)
td_dir = path.join(path.curdir)


class H5cache_class(HasPrivateTraits):
    """
    Cache class that handles opening and closing 'tables.File' objects
    """
    # cache directory
    cache_dir = Str
    
    busy = Bool(False)
    
    open_files = WeakValueDictionary()
    
    open_count = dict()
    
    def get_cache( self, obj, name, mode='a' ):
        while self.busy:
            pass
        self.busy = True
        cname = name + '_cache.h5'
        if isinstance(obj.h5f, tables.File):
            oname = path.basename(obj.h5f.filename)
            print((oname, cname))
            if oname == cname:
                self.busy = False
                return
            else:
                print((oname, self.open_count[oname]))
                self.open_count[oname] = self.open_count[oname] - 1
                # close if no references to file left
                if not self.open_count[oname]:
                    obj.h5f.close()
        # open each file only once
        if not cname in self.open_files:
            obj.h5f = tables.open_file(path.join(self.cache_dir, cname), mode)
            self.open_files[cname] = obj.h5f
        else:
            obj.h5f = self.open_files[cname]
            obj.h5f.flush()
        self.open_count[cname] = self.open_count.get(cname, 0) + 1
        # garbage collection, identify unreferenced open files
        try:
            values = self.open_files.itervalues()
        except AttributeError:
            values = iter(self.open_files.values())
            
        for a in values:
            close_flag = True
            # inspect all refererres to the file object
            for ref in gc.get_referrers(a):
                # does the file object have a referrer that has a 'h5f' 
                # attribute?
                if isinstance(ref,dict) and 'h5f' in ref:
                    # file is still referred, must not be closed
                    close_flag = False
                    break
            # no reference except from its own internal objects
            if close_flag:
                # reset reference count
                self.open_count[path.basename(a.filename)] = 0
                a.close()
        print(list(self.open_count.items()))
        self.busy = False
        
        
H5cache = H5cache_class(cache_dir=cache_dir)
