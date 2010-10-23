"""
Create a temporary directory populated with files and directories and test that
fpath.Dir recognizes children.
"""
import os
import shutil

from fpath import Dir, Path


TEMP_DIR = 'temp_fpath_tests'
NUM_FILES = 10
NUM_DIRS = 5
DIR_FMT = '{0}/dir%03i'.format(TEMP_DIR)
FILE_FMT = '{0}/%03i.txt'.format(TEMP_DIR)


def setup():
    os.mkdir(TEMP_DIR)
    for n in range(NUM_DIRS):
        os.mkdir(DIR_FMT % n)
    for n in range(NUM_FILES):
        open(FILE_FMT % n, 'w').close()

def teardown():
    shutil.rmtree(TEMP_DIR)


def test_num_children():
    d = Dir(TEMP_DIR)
    assert len(list(d.children())) == (NUM_FILES + NUM_DIRS)

def test_num_dirs():
    d = Dir(TEMP_DIR)
    assert len(list(d.walk('d'))) == NUM_DIRS

def test_num_files():
    d = Dir(TEMP_DIR)
    assert len(list(d.walk('f'))) == NUM_FILES

def test_transform_path_to_dir():
    dir_path = Path(TEMP_DIR)
    assert dir_path.transform() == Dir(TEMP_DIR)
    # Comparing equality of Path and Dir only compares their string paths.
    # Check that object was properly transformed using isinstance.
    assert isinstance(dir_path.transform(), Dir)


if __name__ == '__main__':
    import nose
    nose.runmodule()
