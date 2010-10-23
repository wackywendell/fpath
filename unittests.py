import os

from fpath import Path, File, Link, Dir

import unittest
import string
import shutil

class PathManipulation(unittest.TestCase):
    ext = 'ext'
    filename = 'file.ext'
    path_str = '/some/path/'
    file_str = '/some/path/file.ext'
    
    def test_extension(self):
        self.assertEqual(Path(self.file_str).extension, self.ext)
    
    def test_path_indexing(self):
        file_path = Path(self.file_str)
        path_list = self.file_str.split(os.path.sep)
        # When path starts at root, file_path[0] will be root '/', while 
        # path_list[0] will contain an empty string ''; don't compare first index.
        for a, b in zip(file_path[1:], path_list[1:]):
            self.assertEqual(a, b)
        
    def test_home_path(self):
        myhome = Path('~').norm()
        oshome = os.path.expanduser('~')
        self.assertEqual(myhome, oshome)

    def test_dir_init(self):
        dir_path = Path(self.path_str)
        self.assertEqual(Dir(self.path_str), Dir(dir_path))

    def test_file_init(self):
        file_path = Path(self.file_str)
        self.assertEqual(File(self.file_str), File(file_path))

    def test_add_to_path(self):
        d = Dir(self.path_str)
        self.assertEqual((d + self.filename), Path(self.file_str))

    def test_touch(self):
        f = File(self.filename)
        f.touch()
        self.assertTrue(os.path.exists(self.filename))
        self.assertEqual(f.open().read(), '')
        os.remove(self.filename)


    def test_create_path_from_dir(self):
        dir_ = Dir(self.path_str)
        self.assertEqual(Path(dir_), Path(self.path_str))

    def test_create_path_from_file(self):
        file_ = File(self.file_str)
        self.assertEqual(Path(file_), Path(self.file_str))

    def test_create_dir_from_path(self):
        dir_path = Path(self.path_str)
        self.assertEqual(Dir(dir_path), Dir(self.path_str))

    def test_create_file_from_path(self):
        file_path = Path(self.file_str)
        self.assertEqual(File(file_path), File(self.file_str))


    # Comparing equality of Path, File, and Dir only compares their string paths.
    # Check that object was properly transformed using isinstance.
    def test_transform_dir_to_path(self):
        dir_ = Dir(self.path_str)
        self.assertEqual(dir_.transform(), Path(self.path_str))
        self.assertTrue(isinstance(dir_.transform(), Path))

    def test_transform_file_to_path(self):
        file_ = File(self.file_str)
        self.assertEqual(file_.transform(), Path(self.file_str))
        self.assertTrue(isinstance(file_.transform(), Path))

    def test_transform_path_to_dir(self):
        dir_path = Path(self.path_str)
        # Non-existent paths don't get transformed to Dir.
        self.assertTrue(isinstance(dir_path.transform(), Path))

    def test_transform_path_to_file(self):
        file_path = Path(self.file_str)
        # Non-existent paths don't get transformed to File.
        self.assertTrue(isinstance(file_path.transform(), Path))

class TempDir(unittest.TestCase):
    temp_dir = 'temp_fpath_tests'
    num_files = 10
    num_dirs = 5
    
    def dname(self, n):
        return '{}/dir{:03d}i.txt'.format(self.temp_dir, n)
    
    def fname(self, n):
        return '{}/{:03d}i'.format(self.temp_dir, n)

    def setUp(self):
        os.mkdir(self.temp_dir)
        for n in range(self.num_dirs):
            os.mkdir(self.dname(n))
        for n in range(self.num_files):
            open(self.fname(n), 'w').close()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_num_children(self):
        d = Dir(self.temp_dir)
        self.assertEqual(len(list(d.children())), (self.num_files + self.num_dirs))

    def test_num_dirs(self):
        d = Dir(self.temp_dir)
        self.assertEqual(len(list(d.walk('d'))), self.num_dirs)

    def test_num_files(self):
        d = Dir(self.temp_dir)
        self.assertEqual(len(list(d.walk('f'))), self.num_files)

    def test_transform_path_to_dir(self):
        dir_path = Path(self.temp_dir)
        self.assertEqual(dir_path.transform(), Dir(self.temp_dir))
        # Comparing equality of Path and Dir only compares their string paths.
        # Check that object was properly transformed using isinstance.
        self.assertTrue(isinstance(dir_path.transform(), Dir))
        
    def test_abs_path(self):
        d = Path(self.temp_dir).transform()
        self.assertTrue(isinstance(d, Dir))
        pathabs = str(d.abspath())
        osabs = os.path.join(os.getcwd(), self.temp_dir)
        self.assertEqual(pathabs, osabs)

class TempFile(unittest.TestCase):
    ext = 'ext'
    filename = 'file.ext'
    testdir = os.path.abspath('.')

    def setUp(self):
        open(self.filename, 'w').close()

    def tearDown(self):
        os.remove(self.filename)
        
    def test_ext(self):
        f = File(self.filename)
        self.assertEqual(f.extension, self.ext)

    def test_path(self):
        f = File(self.filename)
        self.assertEqual(f.abspath()[:-1], self.testdir)

    def test_read(self):
        f = File(self.filename)

    def test_remove(self):
        f = File(self.filename)
        f.remove()
        self.assertTrue(not os.path.exists(self.filename))
        # Recreate the file so that teardown doesn't raise an error.
        f.touch()

    def test_transform_path_to_file(self):
        file_path = Path(self.filename)
        self.assertEqual(file_path.transform(), File(self.filename))
        # Comparing equality of Path and File only compares their string paths.
        # Check that object was properly transformed using isinstance.
        self.assertTrue(isinstance(file_path.transform(), File))

if __name__ == '__main__':
    unittest.main()
    
