#!/usr/bin/env python
from distutils.core import setup
setup(name='sot-gui',
      version='0.1',
      license='BSD',
      platforms='Linux/MacOSX/Windows',
      description='A GUI tool for StackOfTasks framework',
      long_description='A GUI tool for StackOfTasks framework',
      author='Duong Dang',
      author_email='nddang@laas.fr',
      url='www.laas.fr/~nddang',
      packages=['sotgui',\
                    'sotgui.corba',\
                    'sotgui.corba.hppCorbaServer',\
                    'sotgui.corba.hppCorbaServer__POA'],
      package_dir={'sotgui':'src'},
      data_files = [('bin',['bin/sot_gui'])]
     )


