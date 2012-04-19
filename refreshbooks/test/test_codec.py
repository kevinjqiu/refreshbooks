from mock import patch
from mock import Mock

from refreshbooks.codecs import _get_resource_name_and_mime_type
from refreshbooks.codecs import _collect_file_resources

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
