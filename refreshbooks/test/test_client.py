import re
import mock
from mock import sentinel
from mock import patch

from refreshbooks import client
from refreshbooks.api import default_request_encoder
from refreshbooks.api import default_response_decoder

def test_arbitrary_method():
    request_encoder = mock.Mock()
    request_encoder.return_value = sentinel.request

    transport = mock.Mock()
    transport.return_value = sentinel.transport_response

    response_decoder = mock.Mock()
    response_decoder.return_value = sentinel.response

    test_client = client.Client(
        request_encoder,
        transport,
        response_decoder
    )

    response = test_client.arbitrary.method(id=5)

    assert (('arbitrary.method', ), dict(id=5)) == request_encoder.call_args
    assert ((sentinel.request, ), {}) == transport.call_args
    assert ((sentinel.transport_response, ), {}) == response_decoder.call_args
    assert sentinel.response == response

@patch('mimetypes.guess_type')
def test_method_with_file_resource(mock_guess_type):
    mock_guess_type.return_value = ('image/png', None)
    transport = mock.Mock()
    response_xml = """<response status="ok"></response>"""
    transport.return_value = ({'content-type':'application/xml'}, response_xml)
    file_resource = mock.Mock(spec=file)
    file_resource.read.return_value = '\x00\x01'

    test_client = client.Client(
        default_request_encoder,
        transport,
        default_response_decoder
    )

    test_client.file.upload(
        file=dict(uploaded_by='kevin', file=file_resource)
    )

    class RequestMatcher(object):

        def __eq__(self, other):
            data, headers_factory = other

            if len(headers_factory) != 1:
                return False

            headers_factory = headers_factory[0]

            if not headers_factory.keywords['subtype'] == 'related':
                "The subtype of multipart should be 'related'"
                return False

            boundary = headers_factory.keywords['boundary']
            _, xml_envelope, related_payload, _ = data.split('--%s' % boundary)

            cid_match = re.search(r"cid:([0-9a-f]+)", xml_envelope)

            if not cid_match:
                return False

            cid = cid_match.group(1)
            # make sure Content-ID: <cid> is there in the related part
            if not re.search(r"Content\-ID\:\s\<%s\>" % cid, related_payload):
                return False

            return True

    matcher = RequestMatcher()
    transport.assert_called_with(matcher)
