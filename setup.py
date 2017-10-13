# coding=UTF-8
#------------------------------------------------------------------------------
# Copyright (c) 2007-2016, Acoular Development Team.
#------------------------------------------------------------------------------

from setuptools import setup
from os.path import join, abspath, dirname


#import acoular.version as av
#bf_version = str(av.__version__)
#bf_author = str(av.__author__)

bf_version = "17.10"
bf_author = "Acoular developers"



# Get the long description from the relevant file
here = abspath(dirname(__file__))
with open(join(here, 'README.rst')) as f:
    long_description = f.read()
                    
    
setup(name="acoular", 
      version=bf_version, 
      description="Library for acoustic beamforming",
      long_description=long_description,
      license="BSD",
      author=bf_author,
      author_email="info@acoular.org",
      url="http://www.acoular.org",
      classifiers=[
      'Development Status :: 5 - Production/Stable',
      'Intended Audience :: Education',
      'Intended Audience :: Science/Research',
      'Topic :: Scientific/Engineering :: Physics',
      'License :: OSI Approved :: BSD License',
      'Programming Language :: Python :: 2',
      'Programming Language :: Python :: 2.7',
      'Programming Language :: Python :: 3.4',
      'Programming Language :: Python :: 3.5',
      ],
      keywords='acoustic beamforming microphone array',
      packages = ['acoular'],
      install_requires = [
#      'setuptools',	
#      'pyqt>=4',
#      'numpy>=1.13',
#      'numba >=0.35.0',
#      'scipy>=0.13',
#      'scikit-learn>=0.15',
#      'tables>=3.1',
#      'traits>=4.5.0',
#      'traitsui>=4.4.1',
#      'chaco>=4.4'
	],
      setup_requires = [
#      'setuptools',	
#      'pyqt>=4',
#      'numpy>=1.13',
#      'numba >=0.35.0',
#      'scipy>=0.13',
#      'scikit-learn>=0.15',
#      'tables>=3.1',
#      'traits>=4.5.0',
#      'traitsui>=4.4.1',
#      'chaco>=4.4'
	],
#      ext_modules = [module1],
      scripts=['ResultExplorer.py','CalibHelper.py',
               join('examples','acoular_demo.py')],
      include_package_data = True,
      package_data={'acoular': ['xml/*.xml']}
)

