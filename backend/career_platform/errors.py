from rest_framework.exceptions import APIException


class FeatureNotImplemented(APIException):
    status_code = 501
    default_code = 'FEATURE_NOT_IMPLEMENTED'

    def __init__(self, module, operation):
        super().__init__({'module': module, 'operation': operation})


class Conflict(APIException):
    status_code = 409
    default_detail = '请求与已有记录冲突'
    default_code = 'CONFLICT'


class InvalidModelOutput(APIException):
    status_code = 502
    default_detail = '模型返回内容无效'
    default_code = 'INVALID_MODEL_OUTPUT'


class ModelUnavailable(APIException):
    status_code = 503
    default_detail = '模型服务暂时不可用'
    default_code = 'MODEL_UNAVAILABLE'


class ModelTimeout(APIException):
    status_code = 504
    default_detail = '模型服务响应超时'
    default_code = 'MODEL_TIMEOUT'
