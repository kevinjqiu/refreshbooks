import httplib2

from refreshbooks import exceptions as exc

class Transport(object):
    def __init__(self, url, headers_factory, verify_ssl_cert=True):
        self.client = httplib2.Http()
        self.client.disable_ssl_certificate_validation = not verify_ssl_cert
        self.url = url
        self.headers_factory = headers_factory

    def __call__(self, entity):

        resp, content = self.client.request(
            self.url,
            'POST',
            headers=self.headers_factory(),
            body=entity
        )
        if resp.status >= 400:
            raise exc.TransportException(resp.status, content)

        return content
