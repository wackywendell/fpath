#format PYTHON
# -*- coding: iso-8859-1 -*-
""" fpath.py - provides objects for representations of paths, files, dirs, 
and links.

This module presents 5 main objects: Path, Dir, File, Link, and Stats. A Path 
object is a tuple of directories and finally a possible file name, with useful 
Path operations as methods. Dir, File, and Link all derive from the Path 
object, and have additional methods (such as mkdir, touch, readlink, 
respectively)  that are useful for the type of object that it is. A Stats 
object (made with Stats(some_path_object), Stats(some_path_string), or 
some_path_object.stat()) represents properties of the object at that path, 
which can be read and sometimes set. See object documentation for more help.


Based on Noam Raphael's implementation of a path as tuple, which is in turn 
based on the path module by Jason Orendorff
(http://www.jorendorff.com/articles/python/path)
"""

import os
import stat
import itertools
import string
import shutil

import sys
if sys.version_info[0] > 2:
    unicode = str

class Stats(object):
    """A class for managing the properties of a file or directory.
    
    Properties are read from os.stat(), and set with the appropriate methods.
    """
    def __init__(self, path, usecache = True, followlinks = True):
        """path may be a Path object (or descendant), a str, or unicode path.
        
        With cache enabled, it makes one stat call on creation, and uses that 
        to return each property.
        With cache disabled, no stat() call is made on instantiation, but 
        instead one is required for each property access.
    
    With followlinks = False, an os.lstat() call is used, returning properties 
    on the link file itself instead of the file or directory it is pointing to."""
        self._path = Path(path)
        self._usecache = usecache
        self._followlinks = followlinks
        self._cached = None
        if usecache:
            self._stat()
    
    def _stat(self, force = False):
        """Private method for returning os.stat(), os.lstat(), or cached version, depending on necessity."""
        if not force and self._usecache and self._cached:
            return self._cached
        elif self._followlinks:
            self._cached = os.stat(unicode(self._path))
            return self._cached
        else:
            self._cached = os.lstat(unicode(self._path))
            return self._cached
    
    @property
    def isdir(self):
        return stat.S_ISDIR(self._stat().st_mode)

    @property
    def isfile(self):
        return stat.S_ISREG(self._stat().st_mode)
    
    @property
    def islink(self):
        return stat.S_ISLNK(self._stat().st_mode)
    
    @property
    def mode(self):
        """File permissions"""
        self._stat().st_mode % 0o1000
    
    @mode.setter
    def mode(self, mode):
        os.chmod(unicode(self._path), mode)
        self._stat(True)

    @property
    def owner(self):
        """The owner of the file in a (uid, gid) tuple"""
        return (self._stat().st_uid, self._stat().st_gid)
    
    @owner.setter
    def owner(self, ids):
        (uid, gid) = ids
        os.chown(unicode(self._path), uid, gid)
        self._stat(True)
    
    @property
    def size(self):
        """Size in bytes"""
        return self._stat().st_size

    @property
    def atime(self):
        """Access time.
        
        Access and modification times must be set together using Stat.amtime"""
        s = self._stat()
        return s.st_atime

    @property
    def mtime(self):
        """Modification time.
        
        Access and modification times must be set together using Stat.amtime"""
        s = self._stat()
        return s.st_mtime

    @property
    def amtime(self):
        """Access and modification times in a (atime, mtime) tuple."""
        s = self._stat()
        return (s.st_atime, s.st_mtime)

    @amtime.setter
    def amtime(self, times):
        times = (atime, mtime)
        os.utime(unicode(self._path), (atime, mtime))
        self._stat(True)
    
    @property
    def ctime(self):
        """Creation time"""
        return self._stat().st_ctime


class _BaseRoot(object):
        """ Represents a start location for a path.
        
        A Root is an object which may be the first element of a path tuple,
        and represents from where to start the path.
        
        On posix, there's only one: ROOT (singleton).
        On nt, there are a few:
          CURROOT - the root of the current drive (singleton)
          Drive(letter) - the root of a specific drive
          UnrootedDrive(letter) - the current working directory on a specific
                                  drive
          UNCRoot(host, mountpoint) - a UNC mount point

        The class for each OS has its own root classes, which should inherit
        from _OSBaseRoot.

        str(root) should return the string name of the root. The string should
        identify the root: two root elements with the same string should have
        the same meaning. To allow meaningful sorting of path objects, root
        objects can be compared to strings and other root objects. They are
        smaller than all strings, and are compared with other root objects
        according to their string name.

        Every Root object should contain the "isabs" attribute, which is True
        if changes in the current working directory won't change the meaning
        of the root and False otherwise. (CURROOT and UnrootedDrive aren't
        absolute)
        If isabs is True, it should also implement the abspath() method, which
        should return an absolute path object, equivalent to the root when the
        call was made.
        """
        isabs = None

        def abspath(self):
            if self.isabs:
                raise NotImplementedError('This root is already absolute')
            else:
                raise NotImplementedError('abspath is abstract')

        def __str__(self):
            raise NotImplementedError('__str__ is abstract')

        def __cmp__(self, other):
            if isinstance(other, str):
                return -1
            elif isinstance(other, _BaseRoot):
                return cmp(str(self), str(other))
            else:
                raise TypeError('Comparison not defined')

        def __hash__(self):
            # This allows path objects to be hashable
            return hash(unicode(self))

class BasePath(tuple):
    """ The base, abstract, path type.
    
    The OS-specific path types inherit from it.
    """

    # ----------------------------------------------------------------
    # We start with methods which don't use system calls - they just
    # manipulate paths.

    # _OSBaseRoot should be the base of the OS-specific root classes, which
    # should inherit from _BaseRoot
    _OSBaseRoot = None

    # These string constants should be filled by subclasses - they are real
    # directory names
    _curdir = None
    _pardir = None

    # These string constants are used by default implementations of methods,
    # but are not part of the interface - the whole idea is for the interface
    # to hide those details.
    _sep = None
    _altsep = None

    @staticmethod
    def _parse_str(pathstr):
        # Concrete path classes should implement _parse_str to get a path
        # string and return an iterable over path elements.
        raise NotImplementedError('_parse_str is abstract')

    @classmethod
    def _normalize_elements(cls, elements):
        # This method gets an iterable over path elements.
        # It should return an iterator over normalized path elements -
        # that is, curdir elements should be ignored.
        
        for i, element in enumerate(elements):
            if isinstance(element, str) or isinstance(element, unicode):
                if element != cls._curdir:
                    if (not element or
                        cls._sep in element or
                        (cls._altsep and cls._altsep in element)):
                        # Those elements will cause path(str(x)) != x
                        reason = ''
                        if not element:
                            reason = 'element does not exist.'
                        elif cls._sep in element:
                            reason = 'cls._sep in element.'
                        elif cls._altsep and cls._altsep in element:
                            reason = 'cls._altsep in element.'
                        raise ValueError("Element {0} is invalid: {1}".format(
                                              element, reason))
                    yield element
            elif i == 0 and isinstance(element, cls._OSBaseRoot):
                yield element
            else:
                raise TypeError("Element {0} is of a wrong type".format(element))

    def __new__(cls, arg=None):
        """ Create a new path object.
        
        If arg isn't given, an empty path, which represents the current
        working directory, is returned.
        If arg is already an instance of cls (and not a derived class), arg is returned.
        If arg is a string, it is parsed into a logical path.
        If arg is an iterable over path elements, a new path is created from
        them.
        """
        if arg is None:
            return tuple.__new__(cls)
        if isinstance(arg, cls) and type(arg) is cls:
            return arg
        elif isinstance(arg, BasePath):
            return tuple.__new__(cls, arg)
        elif isinstance(arg, cls._OSBaseRoot):
            return tuple.__new__(cls, (arg,))
        elif isinstance(arg, str) or isinstance(arg, unicode):
            return tuple.__new__(cls, cls._parse_str(arg))
        else:
            return tuple.__new__(cls, cls._normalize_elements(arg))

    def __init__(self, arg=None):
        # Since paths are immutable, we can cache the string representation
        self._cached_str = None

    def _build_str(self):
        # Return a string representation of self.
        # 
        # This is a default implementation, which may be overriden by
        # subclasses (form example, MacPath)
        if not self:
            return self._curdir
        elif isinstance(self[0], self._OSBaseRoot):
            return unicode(self[0]) + self._sep.join(self[1:])
        else:
            return self._sep.join(self)

    def __str__(self):
        """ Return a string representation of self. """
        if self._cached_str is None:
            self._cached_str = self._build_str()
        return str(self._cached_str)
    
    def __unicode__(self):
        """ Return a string representation of self. """
        if self._cached_str is None:
            self._cached_str = self._build_str()
        return self._cached_str

    def __repr__(self):
        # We want path, not the real class name.
        return 'Path(%r)' % str(self)

    @property
    def isabs(self):
        """ Return whether this path represent an absolute path.
        
        An absolute path is a path whose meaning doesn't change when the
        the current working directory changes.
        
        (Note that this is not the same as "not self.isrel")
        """
        return len(self) > 0 and \
               isinstance(self[0], self._OSBaseRoot) and \
               self[0].isabs

    @property
    def isrel(self):
        """ Return whether this path represents a relative path.

        A relative path is a path without a root element, so it can be
        concatenated to other paths.

        (Note that this is not the same as "not self.isabs")
        """
        return len(self) == 0 or \
               not isinstance(self[0], self._OSBaseRoot)

    # Wrap a few tuple methods to return path objects

    def __add__(self, other):
        """A Path can be added to another Path (provided the right operand
        Path is relative), a string, or a tuple (provided the string or
        tuple can be converted to a Path).
        
        In general, the final object will have the class of the right
        operand; if the right operand is a string or tuple, the
        return value will be of class Path."""
        cls = self._Path
        if isinstance(other, BasePath):
            cls = other.__class__
        else:
            other = cls(other)
        if not other.isrel:
            raise ValueError("Right operand should be a relative path")
        return cls(itertools.chain(self, other))

    def __radd__(self, other):
        if not self.isrel:
            raise ValueError("Right operand should be a relative path")
        if not isinstance(other, BasePath):
            other = self.__class__(other)
        return self.__class__(itertools.chain(other, self))
    
    def __getslice__(self, i,j):
        return self.__getitem__(slice(i,j))

    def __getitem__(self, key):
        """A base implementation of __getitem__ that determines 
        whether the slice includes the last element, and calls 
        the appropriate sub-method"""
        tupslice = tuple.__getitem__(self, key)
        if not isinstance(key, slice):
            # in the case a single inner item is requested,
            # return it (as a string, not as a path)
            return tupslice
        start, stop, step = key.indices(len(self))
        stop -= (stop+step-1-start) % step
        if stop >= len(self):
            return self._getatend(tupslice)
        else:
            return self._getnotend(tupslice)
    
    def _getatend(self, tpl):
        """Allows subclasses to define what class is returned
        if the slice requested includes the final path piece"""
        return self.__class__(tpl)
    
    def _getnotend(self, tpl):
        """Allows subclasses to define what class is returned 
        if the slice requested does not include the final path piece"""
        return self._Path(tpl)

    def __mul__(self, *args):
        if not self.isrel:
            raise ValueError("Only relative paths can be multiplied")
        return self.__class__(tuple.__mul__(self, *args))

    def __rmul__(self, *args):
        if not self.isrel:
            raise ValueError("Only relative paths can be multiplied")
        return self.__class__(tuple.__rmul__(self, *args))

    @classmethod
    def __getnorm(cls, pth):
        """Gets a (basically) normalized Path for the object given.
        If the object can not be made into a path, None is returned."""
        try:
            p = cls._Path(pth)
        except:
            return None
        return p.norm(False, False, False)
    
    def __eq__(self, other):
        return tuple.__eq__(self.norm(False, False, False), self.__getnorm(other))
    def __hash__(self):
        return tuple.__hash__(self)
    def __ge__(self, other):
        return tuple.__ge__(self.norm(False, False, False), self.__getnorm(other))
    def __gt__(self, other):
        return tuple.__gt__(self.norm(False, False, False), self.__getnorm(other))
    def __le__(self, other):
        return tuple.__le__(self.norm(False, False, False), self.__getnorm(other))
    def __lt__(self, other):
        return tuple.__lt__(self.norm(False, False, False), self.__getnorm(other))
    def __ne__(self, other):
        return tuple.__ne__(self.norm(False, False, False), self.__getnorm(other))
        

    # ----------------------------------------------------------------
    # Now come the methods which use system calls.

    # --- Path transformation which use system calls

    def abspath(self):
        if not self:
            return self._Dir.cwd()
        if isinstance(self[0], self._OSBaseRoot):
            if self[0].isabs:
                return self
            else:
                return self[0].abspath() + self[1:]
        else:
            return self.__class__(self._Dir.cwd() + self)

    def realpath(self):
        """Returns the canonical path to an object, without any symbolic
        links"""
        return self.__class__(os.path.realpath(unicode(self)))

    def relpathto(self, dst):
        """ Return a relative path from self to dest.

        This method examines self.realpath() and dest.realpath(). If
        they have the same root element, a path in the form
        Path([path.pardir, path.pardir, ..., dir1, dir2, ...])
        is returned. If they have different root elements,
        dest.realpath() is returned.
        """
        src = self.realpath()
        dst = self.__class__(dst).realpath()

        if src[0] == dst[0]:
            # They have the same root
            
            # find the length of the equal prefix
            i = 1
            while i < len(src) and i < len(dst) and \
                  self.normcasestr(src[i]) == self.normcasestr(dst[i]):
                i += 1

            return [self._pardir] * (len(src) - i) + dst[i:]

        else:
            # They don't have the same root
            return dst
            

    # --- Expand
    @property
    def extension(self):
        return ''.join(self[-1].rsplit('.', 1)[1:])

    def norm(self, user=True, vars=True, real=False):
        """Returns a Path object equivalent to self, but normalized
        with respect to case, separators, and (optionally) user
        and home variables."""
        s = unicode(self)
        if user:
            s = os.path.expanduser(s)
        if vars:
            s = os.path.expandvars(s)
        if real:
            s = os.path.realpath(s)
        s = os.path.normcase(s)
        s = os.path.normpath(s)
        return self.__class__(s)
    # --- Info about the path

    def stat(self, usecache = True, followlinks = True):
        """Returns a stat object for this path.
        
        with usecache = True, an os.stat() call is made immediately 
        and cached. As False, an os.stat() call is made for each 
        attribute access.
        
        with followlinks = False, an os.lstat() call is used, 
        returning properties on the link file itself instead of the 
        file or directory it is pointing to."""
        return Stats(self, usecache, followlinks)
    
    def exists(self):
        try:
            self.stat(True)
        except OSError:
            return False
        else:
            return True

    def transform(self, followlinks = True, pathonerr = True):
        """Returns Dir or File object if the path exists.
        
        Determines the type of file located at this path, 
        and returns a File or Dir object if the path is a 
        regular file or directory.
        
        With followlinks = False, a path that is a link to a separate 
        file or folder (or nothing) is returned as a Link object.
        
        With pathonerr = False, paths that do not exist (or are 
        special objects) will raise errors. The default behavior is 
        to return a Path object."""
        try:
            s = self.stat(True, followlinks)
        except OSError:
            if pathonerr:
                return self._Path(self)
            else:
                raise
        
        if s.islink:
            return self._Link(self)
        elif s.isdir:
            return self._Dir(self)
        elif s.isfile:
            return self._File(self)
        else:
            return self._Path(self)
    
    def ismount(self):
        return os.path.ismount(unicode(self))

    # --- Modifying operations on files and directories

    def rename(self, new):
        os.rename(unicode(self), unicode(new))

    # Additional methods in subclasses:
    # chown (PosixPath, XXX MacPath)
    # lchown (PosixPath, XXX MacPath)


    # --- Create/delete operations on directories

    def mkdir(self, mode=0o777, all = False):
        if all:
            os.makedirs(unicode(self), mode)
        else:
            os.mkdir(unicode(self), mode)

    # --- Modifying operations on files
    def remove(self):
        os.remove(unicode(self))

    def copy(self, dst, copystat=False):
        """ Copy file from self to dst.

        If copystat is False, copy data and mode bits ("cp self dst").
        If copystat is True, copy data and all stat info ("cp -p self dst").

        The destination may be a directory. If so, a file with the same base
        name as self will be created in that directory.
        """
        dst = self.__class__(dst)
        if dst.stat().isdir:
            dst += self[-1]
        shutil.copyfile(unicode(self), unicode(dst))
        if copystat:
            shutil.copystat(unicode(self), unicode(dst))
        else:
            shutil.copymode(unicode(self), unicode(dst))

    def move(self, dst):
        dst = self.__class__(dst)
        return shutil.move(unicode(self), unicode(dst))
        

    # --- Links

    # In subclasses:
    # link (PosixPath, XXX MacPath)
    # writelink (PosixPath) - what about MacPath?
    # readlink (PosixPath, XXX MacPath)
    # readlinkpath (PosixPath, XXXMacPath)


    # --- Extra

    # In subclasses:
    # mkfifo (PosixPath, XXX MacPath)
    # mknod (PosixPath, XXX MacPath)
    # chroot (PosixPath, XXX MacPath)
    #
    # startfile (NTPath)

class BaseFile(BasePath):
    def __init__(self, arg):
        return BasePath.__init__(self, arg)

    def __repr__(self):
        return 'File(%r)' % unicode(self)
    def _getnotend(self, tpl):
        """Allows subclasses to define what class is returned if the slice requested does not include the final path piece"""
        return self._Dir(tpl)
        
    def touch(self):
        """ Set the access/modified times of this file to the current time.
        Create the file if it does not exist.
        """
        fd = os.open(unicode(self), os.O_WRONLY | os.O_CREAT, 0o666)
        os.close(fd)
        os.utime(unicode(self), None)

    def open(self, *args, **kwargs):
        """Return a file object that can be read"""
        return open(unicode(self))

    def __add__(self, other):
        raise ValueError("File objects not supported as left operand")

class BaseDir(BasePath):
    def __repr__(self):
        return 'Dir(%r)' % unicode(self)
    def _getnotend(self, tpl):
        """Allows subclasses to define what class is returned if the slice requested does not include the final path piece"""
        return self.__class__(tpl)

    @classmethod
    def cwd(cls):
        """Returns current working directory"""
        return cls(os.getcwd())

    def chdir(self):
        """Changes current working directory to be this directory"""
        return os.chdir(unicode(self))
    
    def remove(self):
        os.rmdir(unicode(self))
    
    def children(self):
        for child in os.listdir(unicode(self)):
            pchild = (self + child)
            yield pchild
        return
        
    def walk(self, mode = 'fd'):
        """Yields subdirectories and files in the path.
        Objects are always yielded after their containing directory.
        
        Mode represents what kind of objects are returned, and
        can be a string containing any of the following characters:
        'd': return directories as Dir objects (otherwise skip)
        'f': return files as File objects (otherwise skip)
        'l': return links as Link objects (otherwise treat as
             the file/directory/etc. it is pointing to)
        'L': skip links, overrides 'l'
        'o': return unrecognized object as Path objects (otherwise skip)

        Special objects (block devices, etc.) are yielded as Path objects.
        """
        dirs = 'd' in mode
        files = 'f' in mode
        skiplinks = 'L' in mode
        links = 'l' in mode or skiplinks
        other = 'o' in mode
        for child in self.children():
            try:
                s = child.stat(usecache=True, followlinks=not links)
            except OSError:
                if other:
                    yield child
                continue
            if s.isdir:
                child = self._Dir(child)
                if dirs:
                    yield child
                for c in child.walk(mode):
                    yield c
            elif s.isfile:
                if files:
                    yield self._File(child)
                continue
            elif s.islink:
                if links:
                    yield self._Link(child)
                continue
            else:
                # what do you do if it isn't a file, link, or dir?
                # I think you yield it anyway, as a path
                yield child

class BaseLink(BasePath):
    def __init__(self, arg):
        return BasePath.__init__(self, arg)

    def __repr__(self):
        return 'Link(%r)' % unicode(self)
    
    def _getnotend(self, tpl):
        """Allows subclasses to define what class is returned if the 
        slice requested does not include the final path piece"""
        return self._Dir(tpl)
    
    def __add__(self, other):
        raise ValueError("Link objects not supported as left operands")

# the associated types that go with it
BasePath._Path = BasePath
BasePath._Dir = BaseDir
BasePath._File = BaseFile
BasePath._Link = BaseLink

class _PosixRoot(_BaseRoot):
    """ Represents the filesystem root (/).
    
    There's only one root on posix systems, so this is a singleton.
    """
    instance = None
    def __new__(cls):
        if cls.instance is None:
            instance = object.__new__(cls)
            cls.instance = instance
        return cls.instance
    
    def __str__(self):
        return '/'

    def __repr__(self):
        return 'Path.Root'

    isabs = True


class PosixPath(BasePath):
    """ Represents POSIX paths. """
    
    _OSBaseRoot = _PosixRoot

    ROOT = _PosixRoot()

    # Public constants
    _curdir = '.'
    _pardir = '..'

    # Private constants
    _sep = '/'
    _altsep = None

    @classmethod
    def _parse_str(cls, pathstr):
        # get a path string and return an iterable over path elements.
        if pathstr.startswith('/'):
            if pathstr.startswith('//') and not pathstr.startswith('///'):
                # Two initial slashes have application-specific meaning
                # in POSIX, and it's not supported currently.
                raise NotImplementedError("Paths with two leading slashes aren't supported.")
            yield cls.ROOT
        for element in pathstr.split('/'):
            if element == '' or element == cls._curdir:
                continue
            # '..' aren't specially treated, since popping the last
            # element isn't correct if the last element was a symbolic
            # link.
            yield element


    # POSIX-specific methods
    

    # --- Info about the path


    def sameas(self, other):
        other = self.__class__(other)
        s1 = self.stat()
        s2 = other.stat()
        return s1.st_ino == s2.st_ino and \
               s1.st_dev == s2.st_dev


    # --- Modifying operations on files and directories

    def chown(self, uid=None, gid=None):
        if uid is None:
            uid = -1
        if gid is None:
            gid = -1
        return os.chown(unicode(self), uid, gid)

    def hardlink(self, newpath):
        """ Create a hard link at 'newpath', pointing to this file. """
        os.link(unicode(self), unicode(newpath))


class PosixFile(PosixPath, BaseFile):
    def mkfifo(self, *args):
        return os.mkfifo(unicode(self), *args)

    def mknod(self, *args):
        return os.mknod(unicode(self), *args)

class PosixDir(PosixPath, BaseDir):
    pass
    
class PosixLink(PosixPath, BaseLink):
    def readlink(self, realpath = False):
        """ Return the path to which this symbolic link points. 
        
        Normally returns a path relative to the link; use
        realpath = True to get a path to the main object"""
        linkpath = self._Path(os.readlink(unicode(self)))
        if linkpath.isrel and realpath:
            return (self[:-1] + linkpath).realpath()
        else:
            return linkpath
    
    def chown(self, uid=None, gid=None):
        """Change ownership of the link file, not its destination"""
        if uid is None:
            uid = -1
        if gid is None:
            gid = -1
        return os.lchown(unicode(self), uid, gid)

    def writelink(self, src):
        """ Create a symbolic link at self, pointing to src.

        src may be any string or Path object. Note that if it's a 
        relative path, it will be interpreted relative to self, not 
        relative to the current working directory.
        """
        os.symlink(unicode(src), unicode(self))

PosixPath._Path = PosixPath
PosixPath._Dir = PosixDir
PosixPath._File = PosixFile
PosixPath._Link = PosixLink

class _NTBaseRoot(_BaseRoot):
    """ The base class of all Windows root classes. """
    pass

class _NTCurRootType(_NTBaseRoot):
    """ Represents the root of the current working drive.
    
    This class is a singleton. It represents the root of the current
    working drive - paths starting with '\'.
    """
    instance = None
    def __new__(cls):
        if cls.instance is None:
            instance = object.__new__(cls)
            cls.instance = instance
        return cls.instance
    
    def __str__(self):
        return '\\'

    def __repr__(self):
        return 'path.CURROOT'

    isabs = False

    def abspath(self):
        from nt import _getfullpathname
        return NTPath(_getfullpathname(unicode(self)))

class NTDrive(_NTBaseRoot):
    """ Represents the root of a specific drive. """
    def __init__(self, letter):
        # Drive letter is normalized - we don't lose any information
        letter = unicode(letter)
        allletters = unicode(string.ascii_letters, 'ascii')
            # I think you can only use ASCII letters for drive names
        if len(letter) != 1 or not letter.isalpha():
            raise ValueError('Should get one letter')
        self._letter = letter.upper()

    @property
    def letter(self):
        # We use a property because we want the object to be immutable.
        return self._letter

    def __str__(self):
        return '{}:\\'.format(self.letter)

    def __repr__(self):
        return 'path.Drive({!r})'.format(self.letter)

    isabs = True

class NTUnrootedDrive(_NTBaseRoot):
    """ Represents the current working directory on a specific drive. """
    def __init__(self, letter):
        # Drive letter is normalized - we don't lose any information
        if len(letter) != 1 or letter not in string.letters:
            raise ValueError('Should get one letter')
        self._letter = letter.lower()

    @property
    def letter(self):
        # We use a property because we want the object to be immutable.
        return self._letter

    def __str__(self):
        return '{0}:'.format(self.letter)

    def __repr__(self):
        return 'Path.UnrootedDrive({1!r})'.format(self.letter)

    isabs = False

    def abspath(self):
        from nt import _getfullpathname
        return NTPath(_getfullpathname(unicode(self)))

class NTUNCRoot(_NTBaseRoot):
    """ Represents a UNC mount point. """
    def __init__(self, host, mountpoint):
        # Host and mountpoint are normalized - we don't lose any information
        self._host = host.lower()
        self._mountpoint = mountpoint.lower()

    @property
    def host(self):
        # We use a property because we want the object to be immutable.
        return self._host

    @property
    def mountpoint(self):
        # We use a property because we want the object to be immutable.
        return self._mountpoint

    def __str__(self):
        return '\\\\{0}\\{1}\\'.format(self.host, self.mountpoint)

    def __repr__(self):
        return 'Path.UNCRoot({0!r}, {1!r})'.format(self.host, self.mountpoint)

    isabs = True

class NTPath(BasePath):
    """ Represents paths on Windows operating systems. """

    _OSBaseRoot = _NTBaseRoot
    
    CURROOT = _NTCurRootType()
    
    Drive = NTDrive
    UnrootedDrive = NTUnrootedDrive
    UNCRoot = NTUNCRoot
    
            
    # Public constants
    _curdir = '.'
    _pardir = '..'

    # Private constants
    _sep = '\\'
    _altsep = '/'

    @staticmethod
    def normcasestr(string):
        """ Normalize the case of one path element.
        
        On Windows, this returns string.lower()
        """
        return string.lower()

    @classmethod
    def _parse_str(cls, pathstr):
        # get a path string and return an iterable over path elements.

        # First, replace all backslashes with slashes.
        # I know that it should have been the other way round, but I can't
        # stand all those escapes.
        
        pathstr = pathstr.replace('\\', '/')

        # Handle the root element
        
        if pathstr.startswith('/'):
            if pathstr.startswith('//'):
                # UNC Path
                if pathstr.startswith('///'):
                    raise ValueError(
                          "Paths can't start with more than two slashes")
                index = pathstr.find('/', 2)
                if index == -1:
                    raise ValueError(
                          "UNC host name should end with a slash")
                index2 = index+1
                while pathstr[index2:index2+1] == '/':
                    index2 += 1
                if index2 == len(pathstr):
                    raise ValueError("UNC mount point is empty")
                index3 = pathstr.find('/', index2)
                if index3 == -1:
                    index3 = len(pathstr)
                yield cls.UNCRoot(pathstr[2:index], pathstr[index2:index3])
                pathstr = pathstr[index3:]
            else:
                # CURROOT
                yield cls.CURROOT
        else:
            if pathstr[1:2] == ':':
                if pathstr[2:3] == '/':
                    # Rooted drive
                    yield cls.Drive(pathstr[0])
                    pathstr = pathstr[3:]
                else:
                    # Unrooted drive
                    yield cls.UnrootedDrive(pathstr[0])
                    pathstr = pathstr[2:]

        # Handle all other elements
        
        for element in pathstr.split('/'):
            if element == '' or element == cls._curdir:
                continue
            # We don't treat pardir specially, since in the presence of
            # links there's nothing to do about them.
            # Windows doesn't have links, but why not keep path handling
            # similiar?
            yield element


    # NT-specific methods

    # --- Extra

    def startfile(self):
        return os.startfile(unicode(self))

    def touch(self):
        """ Set the access/modified times of this file to the current time.
        Create the file if it does not exist.
        """
        fd = os.open(unicode(self), os.O_WRONLY | os.O_CREAT)
        os.close(fd)
        os.utime(unicode(self), None)
    

class NTFile(NTPath, BaseFile):
    pass

class NTDir(NTPath, BaseDir):
    pass

class NTLink(NTPath, BaseLink):
    pass

NTPath._Path = NTPath
NTPath._Dir = NTDir
NTPath._File = NTFile
NTPath._Link = NTLink


if os.name == 'posix':
    Path, File, Dir, Link = PosixPath, PosixFile, PosixDir, PosixLink
    Root = Path.ROOT
elif os.name == 'nt':
    Path, File, Dir, Link = NTPath, NTFile, NTDir, NTLink
    Drive, UnrootedDrive, UNCRoot = NTDrive, NTUnrootedDrive, NTUNCRoot

else:
    raise NotImplementedError(
          "The path object is currently not implemented for OS %r" % os.name)

__all__ = ('Path','File','Dir','Link','Stats')
