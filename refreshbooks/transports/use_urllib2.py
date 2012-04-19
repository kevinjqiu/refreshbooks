import urllib2 as u

from refreshbooks.transports import Transport as _base
from refreshbooks import exceptions as exc


def get_headers_dict(header_lines):
    """urllib2 returns the response headers as a list of lines.
    This function transforms it to a dictionary of {header:value},
    and lower-case all the header fields so we have the same header
    field names across all supported transport layers.

    >>> header_lines = [
    ...    "Date: Thu, 19 Apr 2012 14:43:58 GMT\\r\\n",
    ...    "Server: Apache/2.2.3 (CentOS)\\r\\n",
    ...    "X-Powered-By: PHP/5.3.6\\r\\n",
    ...    "Cache-control: private\\r\\n",
    ...    "Content-Length: 102\\r\\n",
    ...    "Connection: close\\r\\n",
    ...    "Content-Type: application/xml; charset=utf-8\\r\\n"]
    >>> headers = get_headers_dict(header_lines)
    >>> headers['content-length']
    '102'
    >>> headers['cache-control']
    'private'
    >>> headers['content-type']
    'application/xml; charset=utf-8'
    >>> headers['connection']
    'close'
    >>> headers['date']
    'Thu, 19 Apr 2012 14:43:58 GMT'
    >>> headers['x-powered-by']
    'PHP/5.3.6'
    >>> headers['server']
    'Apache/2.2.3 (CentOS)'
    """
    return dict(map(
        lambda (field, value) : (field.lower(), value.strip()),
        [line.split(':', 1) for line in header_lines]))

class Transport(_base):
    def __init__(self, url, headers_factory, verify_ssl_cert=False):
        if verify_ssl_cert:
            # urllib2 doesn't do SSL certificate validation,
            # verify_ssl_cert flag is ignored.
            import warnings
            warnings.warn("urllib2 doesn't support SSL cert verification.")
        super(Transport, self).__init__(url, headers_factory, verify_ssl_cert)

    def __call__(self, request):
        entity, extra_headers = request

        request = u.Request(
            url=self.url,
            data=entity,
            headers=self.build_headers(*extra_headers)
        )
        try:
            fp = u.urlopen(request)
            return get_headers_dict(fp.info().headers), fp.read()
        except u.HTTPError, e:
            raise exc.TransportException(e.code, e.read())
