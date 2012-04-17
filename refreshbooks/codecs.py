import sys
import uuid

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
    if len(args) == 1:
        return adapters.xml_request(*args, **kwargs)

    if len(args) == 2:
        method, request_obj = args

        files = _collect_file_resources(request_obj)

        envelope = adapters.xml_request(*[method, request_obj],
            **kwargs)

        # combine envelope and files in a multipart/related request
        # TODO: delegate this to transport?

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
