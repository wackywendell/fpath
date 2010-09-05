"""
Create a temporary file for some simple tests.
"""
import os

from fpath import File, Path


EXT = 'ext'
FILENAME = 'file.ext'
TESTDIR = os.path.abspath('.')


def setup():
    open(FILENAME, 'w').close()

def teardown():
    os.remove(FILENAME)
    
def test_ext():
    f = File(FILENAME)
    assert f.extension == EXT

def test_path():
    f = File(FILENAME)
    assert f.abspath()[:-1] == TESTDIR

def test_read():
    f = File(FILENAME)

def test_remove():
    f = File(FILENAME)
    f.remove()
    assert not os.path.exists(FILENAME)
    # Recreate the file so that teardown doesn't raise an error.
    f.touch()

def test_transform_path_to_file():
    file_path = Path(FILENAME)
    assert file_path.transform() == File(FILENAME)
    # Comparing equality of Path and File only compares their string paths.
    # Check that object was properly transformed using isinstance.
    assert isinstance(file_path.transform(), File)


if __name__ == '__main__':
    import nose
    nose.runmodule()
