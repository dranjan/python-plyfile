from io import BytesIO

import pytest

from plyfile import PlyData, PlyElementParseError


@pytest.mark.parametrize('valid', [True, False])
def test_read_ascii_leaves_caller_binary_stream_open(valid):
    payload = (b'ply\nformat ascii 1.0\nelement vertex 1\n'
               b'property float x\nend_header\n')
    payload += b'1\n' if valid else b'invalid\n'
    stream = BytesIO(payload)
    if valid:
        data = PlyData.read(stream)
        assert data['vertex']['x'][0] == 1
    else:
        with pytest.raises(PlyElementParseError):
            PlyData.read(stream)
    assert not stream.closed
    stream.seek(0)
    assert stream.read() == payload
