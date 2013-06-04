from distutils.core import setup
import os

def getfile(fname):
    return open(os.path.join(os.path.dirname(__file__), fname))

readme = getfile('README.txt').read()

setup(name='fpath',
      version='0.7',
      description='Filesystem paths as objects',
      author='Wendell',
      author_email='wackywendell@gmail.com',
      py_modules=['fpath'],
      classifiers=[ # available at http://pypi.python.org/pypi?%3Aaction=list_classifiers
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries',
          'Topic :: System :: Filesystems',
          'Operating System :: POSIX',
          'Operating System :: Microsoft',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3'
        ],
      license='MIT',
      long_description=readme
      )

