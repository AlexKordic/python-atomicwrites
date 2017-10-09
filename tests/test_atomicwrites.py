import errno
import os

from atomicwrites import atomic_write

import pytest


def test_atomic_write(tmpdir):
    fname = tmpdir.join('ha')
    for i in range(2):
        with atomic_write(str(fname), overwrite=True) as f:
            f.write('hoho')

    with pytest.raises(OSError) as excinfo:
        with atomic_write(str(fname), overwrite=False) as f:
            f.write('haha')

    assert excinfo.value.errno == errno.EEXIST

    assert fname.read() == 'hoho'
    assert len(tmpdir.listdir()) == 1


def test_teardown(tmpdir):
    fname = tmpdir.join('ha')
    with pytest.raises(AssertionError):
        with atomic_write(str(fname), overwrite=True):
            assert False

    assert not tmpdir.listdir()


def test_replace_simultaneously_created_file(tmpdir):
    fname = tmpdir.join('ha')
    with atomic_write(str(fname), overwrite=True) as f:
        f.write('hoho')
        fname.write('harhar')
        assert fname.read() == 'harhar'
    assert fname.read() == 'hoho'
    assert len(tmpdir.listdir()) == 1


def test_dont_remove_simultaneously_created_file(tmpdir):
    fname = tmpdir.join('ha')
    with pytest.raises(OSError) as excinfo:
        with atomic_write(str(fname), overwrite=False) as f:
            f.write('hoho')
            fname.write('harhar')
            assert fname.read() == 'harhar'

    assert excinfo.value.errno == errno.EEXIST
    assert fname.read() == 'harhar'
    assert len(tmpdir.listdir()) == 1


# Verify that nested exceptions during rollback do not overwrite the initial
# exception that triggered a rollback.
def test_open_reraise(tmpdir):
    fname = tmpdir.join('ha')
    with pytest.raises(AssertionError):
        with atomic_write(str(fname), overwrite=False) as f:
            # Mess with f, so rollback will trigger an OSError. We're testing
            # that the initial AssertionError triggered below is propagated up
            # the stack, not the second exception triggered during rollback.
            f.name = "asdf"
            # Now trigger our own exception.
            assert False, "Intentional failure for testing purposes"


def test_atomic_write_in_pwd(tmpdir):
    orig_curdir = os.getcwd()
    try:
        os.chdir(str(tmpdir))
        fname = 'ha'
        for i in range(2):
            with atomic_write(str(fname), overwrite=True) as f:
                f.write('hoho')

        with pytest.raises(OSError) as excinfo:
            with atomic_write(str(fname), overwrite=False) as f:
                f.write('haha')

        assert excinfo.value.errno == errno.EEXIST

        assert open(fname).read() == 'hoho'
        assert len(tmpdir.listdir()) == 1
    finally:
        os.chdir(orig_curdir)

def test_jpeg_write(tmpdir):
    input_jpeg = os.path.abspath(os.path.join(os.path.dirname(__file__), "alex.jpg"))
    output_jpeg = str(tmpdir.join('corrupted.jpg'))
    with open(input_jpeg, "rb") as i:
        data = i.read()
    with atomic_write(output_jpeg, overwrite=True, mode="wb") as f:
        f.write(data)
    written_data = open(output_jpeg, "rb").read()
    original_data = open(input_jpeg, "rb").read()
    assert written_data == original_data
