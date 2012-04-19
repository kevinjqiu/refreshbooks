import httplib2

from refreshbooks.transports import Transport as _base
from refreshbooks import exceptions as exc

class Transport(_base):
    def __init__(self, url, headers_factory, verify_ssl_cert=True):
        super(Transport, self).__init__(url, headers_factory, verify_ssl_cert)
        self.client = httplib2.Http()
        self.client.disable_ssl_certificate_validation = not verify_ssl_cert

    def __call__(self, request):
        entity, extra_headers = request

        resp, content = self.client.request(
            self.url,
            'POST',
            headers=self.build_headers(*extra_headers),
            body=entity
        )

        if resp.status >= 400:
            raise exc.TransportException(resp.status, content)

        return resp, content
