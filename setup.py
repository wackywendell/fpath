from distutils.core import setup
import os

# Work around mbcs bug in distutils.
# http://bugs.python.org/issue10945
import codecs
try:
    codecs.lookup('mbcs')
except LookupError:
    ascii = codecs.lookup('ascii')
    func = lambda name, enc=ascii: {True: enc}.get(name=='mbcs')
    codecs.register(func) 

def getfile(fname):
    return open(os.path.join(os.path.dirname(__file__), fname))

readme = getfile('README.TXT').read()

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
      long_description=readme,
      url='https://pypi.python.org/pypi?name=fpath'
      )

