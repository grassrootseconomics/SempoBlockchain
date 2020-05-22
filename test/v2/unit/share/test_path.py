# platform imports
from share import path

def test_reverse_split():
    """
    GIVEN different paths with one or two elements and all sorts of slashing
    WHEN splitting them
    THEN only non-empty path parts are left
    """
    assert path.reverse_split('foo') == ['foo']
    assert path.reverse_split('/foo') == ['foo']
    assert path.reverse_split('/foo/') == ['foo']
    assert path.reverse_split('/foo/bar') == ['foo', 'bar']
    assert path.reverse_split('/foo/bar/') == ['foo', 'bar']
    assert path.reverse_split('/foo/bar//') == ['foo', 'bar']
    assert path.reverse_split('/foo//bar') == ['foo', 'bar']
