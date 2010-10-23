Description
===========

This module provides 4 objects, Path, File, Link, and Dir, that provide easy
manipulation of path objects.

The main class, Path, represents a path on the filesystem. It is a subclass
of tuple, with directories as entries and the final entry being the file name,
allowing slices to give pieces of the Path object.

The methods of these four objects pretty much cover all the functionality of 
the os and os.path modules, in a far more convenient and object-oriented
fashion.

Example
=======
>>> from fpath import Path, File, Link, Dir
>>> p = Path('~')
>>> p.norm() # gives a normalized version of the path
Path('/home/wendell')
>>> p = p.norm().transform() # 'transform' looks at the type of file, and
                             # returns a Dir, File, or Link object based
                             # upon what is in the filesystem
>>> p
Dir(u'/home/wendell')
>>> p + 'test.txt'           # strings, tuples of strings, and other Paths
                             # can be added to Paths
Path('/home/wendell/test.txt')
>>> d=Dir(p + 'scripts')
>>> len(list(d.children()))
160                          # My scripts directory has 160 entries in it
>>> len(list(d.walk('f')))
550                          # My scripts directory has 550 files (not 
                             # directories) in it, including in sub-dirs
>>> f = File(p + 'test.txt')
>>> f.touch()
>>> f.extension
'txt'
>>> f[-1]                    # Paths are subclasses of Tuple, and slicing
                             # can be really useful
'test.txt'
>>> f[:-1]
Dir(u'/home/wendell')
>>> myfile = f.open()
>>> myfile.read()
''
>>> myfile.close()
>>> f.remove()
>>> f.transform()
Path('/home/wendell/test.txt')

For more information, look at the doc strings - they are extensive.

Basis
=====

This is in response to PEP 355: http://www.python.org/dev/peps/pep-0355/
PEP 355 "lingered", but was rejected based on the fact that the proposed form
was the "ultimate kitchen sink" - it had too many methods. This form is vastly
different, in that it is a subclass of tuple and not str, and splits methods
based on whether they are general path methods, or specific to links, files, or
dirs, and as such, is far more useable. Methods have been kept to a bare 
minimum while still remaining complete.

More Information and Bugs
=========================
At the current version (0.6), Posix, Windows, and Mac paths are supported,
and has been tested on both Windows and Linux.
Please report any bugs:
http://github.com/wackywendell/fpath

Also available through pypi:
http://pypi.python.org/pypi/fpath
