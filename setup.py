from distutils.core import setup
setup(name='fpath',
      version='0.1',
      description='Filesystem paths as objects',
      author='Wendell',
      author_email='wackywendell@gmail.com',
      py_modules=['fpath'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries',
          'Topic :: System :: Filesystems',
          'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)'
        ],
      license='LGPL',
      long_description=open('README.txt').read()
      )

