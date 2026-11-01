from rest_framework.exceptions import APIException


class FeatureNotImplemented(APIException):
    status_code = 501
    default_code = 'FEATURE_NOT_IMPLEMENTED'

    def __init__(self, module, operation):
        super().__init__({'module': module, 'operation': operation})
