import base64

from functools import partial
from refreshbooks import exceptions

try:
    from refreshbooks.optional import oauth as os

    OAuthAuthorization = os.OAuthAuthorization
except ImportError:
    def OAuthAuthorization(consumer, token, sig_method=None):
        raise NotImplementedError('oauth support requires the "oauth" module.')

try:
    from refreshbooks.transports import use_requests as transport
except ImportError:
    try:
        from refreshbooks.transports import use_httplib2 as transport
    except ImportError:
        import warnings
        warnings.warn(
            "Unable to load requests or httplib2 transports, falling back to urllib2. SSL cert verification disabled."
        )
        from refreshbooks.transports import use_urllib2 as transport

class TokenAuthorization(object):
    """Generates HTTP BASIC authentication headers obeying FreshBooks'
    token-based auth scheme (token as username, password irrelevant).

        >>> auth = TokenAuthorization("monkey")
        >>> auth()
        {'Authorization': 'Basic bW9ua2V5Og=='}

    Prefer OAuthAuthorization, from refreshbooks.optional.oauth, for new
    development.
    """
    def __init__(self, token):
        # See RFC 2617.
        base64_user_pass = base64.b64encode("%s:" % (token, ))

        self.headers = {
            'Authorization': 'Basic %s' % (base64_user_pass, )
        }

    def __call__(self):
        return self.headers

class HeadersFactory(object):

    def __init__(self, base_headers_factory, headers):
        self.base_headers_factory = base_headers_factory
        self.headers = headers

    def __call__(self):
        headers = self.base_headers_factory()
        for key, value in self.headers.iteritems():
            headers[key] = value
        return headers

UserAgentHeaders = lambda base_headers_factory, user_agent : \
    HeadersFactory(base_headers_factory, {'User-Agent':user_agent})

KeepAliveHeaders = partial(HeadersFactory, headers={'Connection':'Keep-Alive'})

MultipartContentTypeHeaders = \
    lambda base_headers_factory, subtype, boundary : \
        HeadersFactory(base_headers_factory,
            {'Content-Type':'multipart/%s; boundary="%s"' % (subtype, boundary)})

HttpTransport = transport.Transport
TransportException = exceptions.TransportException
