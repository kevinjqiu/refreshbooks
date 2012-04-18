import sys
import uuid
import mimetypes

from lxml import objectify
from refreshbooks import adapters

def _collect_file_resources(request_obj):
    """Traverse the request object,
    collect the file-like objects in the return value,
    and replace the file value with cid:XXXX.
    """
    iteritems = request_obj.iteritems()

    retval = {}
    for key, value in iteritems:
        if isinstance(value, dict):
            retval.update(_collect_file_resources(value))
        elif isinstance(value, file):
            # generate a unique cid
            cid = uuid.uuid4().hex
            retval[cid] = value
            request_obj[key] = 'cid:%s' % cid
    return retval

def universal_request_encoder(*args, **kwargs):
    # look for anything that looks like
    # a file in the request object.
    method = args[0]
    request_obj = kwargs.values()[0]
    files = _collect_file_resources(request_obj)

    envelope = adapters.xml_request(
        method,
        **kwargs)

    boundary = uuid.uuid4().hex

    if len(files) > 0:
        lines = ["multipart posting",
            "--%s" % boundary,
            "Content-Type: application/xml",
            "",
            '<?xml version="1.0" encoding="utf-8"?>\n'+envelope,
        ]

        for cid, file_to_upload in files.iteritems():
            filename = file_to_upload.name
            mimetype, _ = mimetypes.guess_type(filename)
            lines.append("--%s" % boundary)
            lines.append("Content-Type: %s" % mimetype)
            lines.append('Content-Disposition: attachment; filename="%s"' % filename)
            lines.append("Content-ID: <%s>" % cid)
            lines.append('')
            lines.append(file_to_upload.read())
            lines.append('')
            file_to_upload.close()

        lines.append("--%s" % boundary)
        lines.append('')

    data = '\r\n'.join(lines)

    return data, boundary

def default_request_encoder(*args, **kwargs):
    return adapters.xml_request(*args, **kwargs)

def default_response_decoder(*args, **kwargs):
    headers, content = args[0]

    if headers['content-type'].startswith('application/xml'):
        return adapters.fail_to_exception_response(
            objectify.fromstring(content, **kwargs)
        )
    else:
        # import base64
        # return base64.b64encode(content)
        return content

def logging_request_encoder(method, **params):
    encoded = default_request_encoder(method, **params)

    print >>sys.stderr, "--- Request (%r, %r) ---" % (method, params)
    print >>sys.stderr, encoded

    return encoded

def logging_response_decoder(response):
    print >>sys.stderr, "--- Response ---"
    print >>sys.stderr, response

    return default_response_decoder(response)
