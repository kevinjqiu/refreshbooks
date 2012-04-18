import requests

from refreshbooks import exceptions as exc

class Transport(object):
    def __init__(self, url, headers_factory, verify_ssl_cert=True):
        self.url = url
        self.headers_factory = headers_factory
        self.verify_ssl_cert = verify_ssl_cert

    def __call__(self, entity, *extra_headers):
        headers_factory = self.headers_factory
        for header in extra_headers:
            headers_factory = header(headers_factory)

        resp = requests.post(
            self.url,
            headers=headers_factory(),
            data=entity,
            verify=self.verify_ssl_cert
        )

        if resp.status_code >= 400:
            raise exc.TransportException(resp.status_code, resp.content)

        return resp.headers, resp.content
