import socket
from unittest.mock import patch
from django.test.runner import DiscoverRunner


class FixedAcceptanceRunner(DiscoverRunner):
    def run_suite(self, suite, **kwargs):
        if suite.countTestCases()==0:
            raise RuntimeError('Acceptance suite cannot be empty')
        original=socket.socket.connect
        def offline(sock,address):
            if isinstance(address,tuple) and address[0] not in ('127.0.0.1','::1','localhost'):
                raise AssertionError('Acceptance tests cannot connect to external services')
            return original(sock,address)
        with patch.object(socket.socket,'connect',offline):
            return super().run_suite(suite,**kwargs)

    def suite_result(self,suite,result,**kwargs):
        return super().suite_result(suite,result,**kwargs) + len(result.skipped)
