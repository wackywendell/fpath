import os

from fpath import Path, File, Link, Dir


EXT = 'ext'
FILENAME = 'file.ext'
PATH_STR = '/some/path/'
FILE_STR = '/some/path/file.ext'


def test_path_indexing():
    file_path = Path(FILE_STR)
    path_list = FILE_STR.split(os.path.sep)
    # When path starts at root, file_path[0] will be root '/', while 
    # path_list[0] will contain an empty string ''; don't compare first index.
    for a, b in zip(file_path[1:], path_list[1:]):
        assert a == b
    
def test_home_path():
    dir_path = Path('~')
    assert os.path.expanduser('~') == dir_path.norm()

def test_dir_init():
    dir_path = Path(PATH_STR)
    assert Dir(PATH_STR) == Dir(dir_path)

def test_file_init():
    file_path = Path(FILE_STR)
    assert File(FILE_STR) == File(file_path)

def test_add_to_path():
    d = Dir(PATH_STR)
    assert (d + FILENAME) == Path(FILE_STR)

def test_touch():
    f = File(FILENAME)
    f.touch()
    assert os.path.exists(FILENAME)
    assert f.open().read() == ''
    os.remove(FILENAME)


def test_create_path_from_dir():
    dir_ = Dir(PATH_STR)
    assert Path(dir_) == Path(PATH_STR)

def test_create_path_from_file():
    file_ = File(FILE_STR)
    assert Path(file_) == Path(FILE_STR)

def test_create_dir_from_path():
    dir_path = Path(PATH_STR)
    assert Dir(dir_path) == Dir(PATH_STR)

def test_create_file_from_path():
    file_path = Path(FILE_STR)
    assert File(file_path) == File(FILE_STR)


# Comparing equality of Path, File, and Dir only compares their string paths.
# Check that object was properly transformed using isinstance.
def test_transform_dir_to_path():
    dir_ = Dir(PATH_STR)
    assert dir_.transform() == Path(PATH_STR)
    assert isinstance(dir_.transform(), Path)

def test_transform_file_to_path():
    file_ = File(FILE_STR)
    assert file_.transform() == Path(FILE_STR)
    assert isinstance(file_.transform(), Path)

def test_transform_path_to_dir():
    dir_path = Path(PATH_STR)
    # Non-existent paths don't get transformed to Dir.
    assert isinstance(dir_path.transform(), Path)

def test_transform_path_to_file():
    file_path = Path(FILE_STR)
    # Non-existent paths don't get transformed to File.
    assert isinstance(file_path.transform(), Path)


if __name__ == '__main__':
    import nose
    nose.runmodule()
    