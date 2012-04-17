import urllib2 as u

from refreshbooks import exceptions as exc

class Transport(object):
    def __init__(self, url, headers_factory, verify_ssl_cert=False):
        if verify_ssl_cert:
            # urllib2 doesn't do SSL certificate validation,
            # verify_ssl_cert flag is ignored.
            import warnings
            warnings.warn("urllib2 doesn't support SSL cert verification.")
        self.url = url
        self.headers_factory = headers_factory

    def __call__(self, entity):
        request = u.Request(
            url=self.url,
            data=entity,
            headers=self.headers_factory()
        )
        try:
            fp = u.urlopen(request)
            headers = dict(
                x.strip().split(':')
                for x in fp.info().headers
            )
            return headers, fp.read()
        except u.HTTPError, e:
            raise exc.TransportException(e.code, e.read())
