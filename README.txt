This module provides 4 objects, Path, File, Link, and Dir, that provide easy
manipulation of path objects.

The main class, Path, represents a path on the filesystem. It is a subclass
of tuple, with directories as entries and the final entry being the file name,
allowing slices to give pieces of the Path object.

Some examples:

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
>>> f = File(p + 'test.txt')
>>> f.touch()
>>> f.extension
'txt'
>>> f[-1]
'test.txt'
>>> f[:-1]
Dir(u'/home/wendell')
>>> myfile = f.open()
>>> myfile.read()
''
>>> myfile.close()
>>> f.remove()
>>> f
File(u'/home/wendell/test.txt')
>>> f.transform()
Path('/home/wendell/test.txt')

For more information, look at the doc strings - they are extensive.

At the current version (0.1), Posix, Windows, and Mac paths are supported,
although neither the Windows and Mac versions are complete - please report any
bugs!
