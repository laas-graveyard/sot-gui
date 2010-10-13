#!/usr/bin/env python
from distutils.core import setup
setup(name='sot-gui',
      version='1.0',
      license='L-GPL3',
      platforms='Linux/MacOSX/Windows',
      description='A GUI tool for StackOfTasks framework',
      long_description='A GUI tool for StackOfTasks framework',
      author='Duong Dang',
      author_email='nddang@laas.fr',
      url='www.laas.fr/~nddang',
      packages=['sotgui',\
                    'sotgui.idl',\
                    'sotgui.idl.CorbaServer',\
                    'sotgui.idl.CorbaServer__POA'],
      package_dir={'sotgui':'src'},
      package_data={'sotgui': ['main.xml','text.xml']},
      data_files = [('bin',['src/sot-gui2.py'])],
      requires = ["gtkgl",'pygtk']
     )


