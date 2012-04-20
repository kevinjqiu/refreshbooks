from mock import patch
from mock import Mock

from refreshbooks.codecs import _get_resource_name_and_mime_type
from refreshbooks.codecs import _collect_file_resources
from refreshbooks.codecs import _encode_multipart_request

RANDOM_UUID_MOCK = Mock(hex='a4b420939be842a186f0ea1ecbc4baa3')

extract_cid = lambda value : value.split('cid:')[-1]

@patch('uuid.uuid4')
def test_get_resource_name_and_type___stringio(uuid4):
    uuid4.return_value = RANDOM_UUID_MOCK

    from StringIO import StringIO
    resource = StringIO('GIF89a')
    filename, mimetype = _get_resource_name_and_mime_type(resource)
    assert filename == 'a4b420939be842a186f0ea1ecbc4baa3.gif'
    assert mimetype == 'image/gif'

@patch('uuid.uuid4')
def test_get_resource_name_and_type___cstringio(uuid4):
    uuid4.return_value = RANDOM_UUID_MOCK

    from cStringIO import StringIO
    resource = StringIO('GIF89a')
    filename, mimetype = _get_resource_name_and_mime_type(resource)
    assert filename == 'a4b420939be842a186f0ea1ecbc4baa3.gif'
    assert mimetype == 'image/gif'

def test_get_resource_name_and_type___file_like_object_with_name():
    resource = Mock(spec=file)
    resource.name = 'sample.png'
    filename, mimetype = _get_resource_name_and_mime_type(resource)
    assert filename == 'sample.png'
    assert mimetype == 'image/png'

def test_collect_file_resources___different_types():
    from StringIO import StringIO as SIO
    from cStringIO import StringIO as cSIO

    file_obj = Mock(spec=file)
    sio_obj = SIO('GIF89a')
    csio_obj = cSIO('GIF89a')

    request_obj = dict(
        folder=dict(
            name='mordor',
            pic=file_obj,
            hd=sio_obj,
            ld=csio_obj
        )
    )

    file_cid_map = _collect_file_resources(request_obj)
    assert type(request_obj['folder']['pic']) == str
    assert type(request_obj['folder']['hd']) == str
    assert type(request_obj['folder']['ld']) == str

    assert file_cid_map[extract_cid(request_obj['folder']['pic'])] == file_obj
    assert file_cid_map[extract_cid(request_obj['folder']['hd'])] == sio_obj
    assert file_cid_map[extract_cid(request_obj['folder']['ld'])] == csio_obj

def test_collect_file_resources___nested():
    pic_obj1 = Mock(spec=file)
    pic_obj2 = Mock(spec=file)

    request_obj = dict(
        folder=dict(
            name='mordor',
            pic = pic_obj1,
            child=dict(
                name='gondor',
                pic = pic_obj2
            )
        )
    )

    file_cid_map = _collect_file_resources(request_obj)
    assert type(request_obj['folder']['pic']) == str
    assert type(request_obj['folder']['child']['pic']) == str

    assert file_cid_map[extract_cid(request_obj['folder']['pic'])] == pic_obj1
    assert file_cid_map[extract_cid(request_obj['folder']['child']['pic'])] == pic_obj2

@patch('refreshbooks.codecs._get_resource_name_and_mime_type')
def test_encode_multipart_request(mock_resource_detect):
    from StringIO import StringIO

    mock_resource_detect.return_value = ('avatar.png', 'image/png')
    boundary = 'CUL-DE-SAC'
    xml_envelope = "".join([
        '<request method="awesome.method">',
        '<profile>',
        '<name>foobar</name>',
        '<avatar>cid:ebenezer</avatar>',
        '</profile>',
        '</request>'])

    cid_file_map = {
        'ebenezer' : StringIO('\x00\x01\x02')
    }

    expected = "\r\n".join([
        'multipart posting',
        '--CUL-DE-SAC',
        'Content-Type: application/xml',
        '',
        '<?xml version="1.0" encoding="utf-8"?>\n'+xml_envelope,
        '--CUL-DE-SAC',
        'Content-Type: image/png',
        'Content-Disposition: attachment; filename="avatar.png"',
        'Content-ID: <ebenezer>',
        '',
        '\x00\x01\x02',
        '',
        '--CUL-DE-SAC',
        ''])

    content, headers_factory = _encode_multipart_request(xml_envelope, cid_file_map, boundary)

    assert expected == content
    assert len(headers_factory) == 1
    assert headers_factory[0].keywords == {'subtype':'related', 'boundary':'CUL-DE-SAC'}
