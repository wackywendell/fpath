from distutils.core import setup
setup(name='fpath',
      version='0.1',
      description='Provides objects representing filesystem paths.',
      author='Wendell',
      author_email='wackywendell@gmail.com',
      py_modules=['fpath'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries',
          'Topic :: System :: Filesystems'
        ],
      license='LGPL',
      long_description=open('README.txt').read()
      )

