# platform imports
from share import path

def test_reverse_split():
    assert path.reverse_split('foo') == ['foo']
    assert path.reverse_split('/foo') == ['foo']
    assert path.reverse_split('/foo/') == ['foo']
    assert path.reverse_split('/foo/bar') == ['foo', 'bar']
    assert path.reverse_split('/foo/bar/') == ['foo', 'bar']
    assert path.reverse_split('/foo/bar//') == ['foo', 'bar']
    assert path.reverse_split('/foo//bar') == ['foo', 'bar']
