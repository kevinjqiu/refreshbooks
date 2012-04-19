class Transport(object):

    def __init__(self, url, headers_factory, verify_ssl_cert=True):
        self.url = url
        self.headers_factory = headers_factory
        self.verify_ssl_cert = verify_ssl_cert

    def build_headers(self, *extra_headers):
        headers_factory = self.headers_factory
        for header in extra_headers:
            headers_factory = header(headers_factory)
        return headers_factory()
