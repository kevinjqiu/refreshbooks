import requests

from refreshbooks.transports import Transport as _base
from refreshbooks import exceptions as exc

class Transport(_base):
    def __init__(self, url, headers_factory, verify_ssl_cert=True):
        super(Transport, self).__init__(url, headers_factory, verify_ssl_cert)

    def __call__(self, request):
        entity, extra_headers = request

        resp = requests.post(
            self.url,
            headers=self.build_headers(*extra_headers),
            data=entity,
            verify=self.verify_ssl_cert
        )

        if resp.status_code >= 400:
            raise exc.TransportException(resp.status_code, resp.content)

        return resp.headers, resp.content
