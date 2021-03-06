import sys
import uuid
import mimetypes
import imghdr

from functools import partial
from lxml import objectify
from refreshbooks import adapters
from refreshbooks.transport import MultipartContentTypeHeaders

def _collect_file_resources(request_obj):
    """Traverse the request object,
    collect file-like objects in the return value,
    and replace the file value with cid:XXXX.
    """
    iteritems = request_obj.iteritems()

    retval = {}
    for key, value in iteritems:
        if isinstance(value, dict):
            retval.update(_collect_file_resources(value))
        elif hasattr(value, 'read') and callable(value.read):
            # file-like objects, such as StringIO or CStringIO
            # are acceptable.
            cid = uuid.uuid4().hex
            retval[cid] = value
            request_obj[key] = 'cid:%s' % cid
    return retval

def _get_resource_name_and_mime_type(resource):
    if hasattr(resource, 'name'):
        filename = resource.name
        mimetype, _ = mimetypes.guess_type(filename)
    else:
        img_type = imghdr.what(resource)
        if img_type is None:
            mimetype = 'application/octet-stream'
            img_type = 'bin'
        else:
            mimetype = 'image/%s' % img_type
        filename = ".".join((uuid.uuid4().hex, img_type))

    return filename, mimetype

def _encode_multipart_request(xml_envelope, cid_file_map, boundary):
    # create multipart/related chunks
    lines = ["multipart posting",
        "--%s" % boundary,
        "Content-Type: application/xml",
        "",
        '<?xml version="1.0" encoding="utf-8"?>\n'+xml_envelope,
    ]

    for cid, resource in cid_file_map.iteritems():
        filename, mimetype = _get_resource_name_and_mime_type(resource)

        lines.append("--%s" % boundary)
        lines.append("Content-Type: %s" % mimetype)
        lines.append('Content-Disposition: attachment; filename="%s"' % filename)
        lines.append("Content-ID: <%s>" % cid)
        lines.append('')
        lines.append(resource.read())
        lines.append('')
        resource.close()

    lines.append("--%s" % boundary)
    lines.append('')

    entity = '\r\n'.join(lines)

    # When there are files to upload, we need to
    # change the content-type to multipart/related.
    headers_factory = partial(MultipartContentTypeHeaders,
                        subtype='related',
                        boundary=boundary)
    return entity, [headers_factory]

def default_request_encoder(*args, **kwargs):
    """
    request_encoder returns a tuple:
        (entity, *headers_factory)
    """
    method = args[0]

    # look for anything that looks like
    # a file resource in the argument.
    files = _collect_file_resources(kwargs)

    # the envelope is always sent as xml
    envelope = adapters.xml_request(method, **kwargs)

    if len(files) == 0:
        # Regular request, no files to upload.
        # No extra headers are added
        return envelope, []
    else:
        return _encode_multipart_request(
            envelope,
            files,
            boundary=uuid.uuid4().hex)

def default_response_decoder(*args, **kwargs):
    headers, content = args[0]

    content_type = headers['content-type'].split(';', 1)[0]
    if content_type == 'application/xml':
        return adapters.fail_to_exception_response(
            objectify.fromstring(content, **kwargs)
        )
    else:
        return (headers, content)

def logging_request_encoder(method, **params):
    encoded = default_request_encoder(method, **params)

    print >>sys.stderr, "--- Request (%r, %r) ---" % (method, params)
    print >>sys.stderr, encoded

    return encoded

def logging_response_decoder(response):
    print >>sys.stderr, "--- Response ---"
    print >>sys.stderr, response

    return default_response_decoder(response)
