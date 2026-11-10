from .repository import DjangoPracticeRepository


class PracticeService:
    def __init__(self, *, repository=None, model_gateway=None):
        self.repository = repository or DjangoPracticeRepository()
        self.model_gateway = model_gateway

    def start(self, *, user, data: dict) -> dict:
        return self.repository.start(user=user, data=data)

    def list_sessions(self, *, user, data: dict) -> dict:
        return self.repository.list_sessions(user=user, data=data)

    def get_session(self, *, user, data: dict) -> dict:
        return self.repository.get_session(user=user, session_id=data['id'])

    def record_answer(self, *, user, data: dict) -> dict:
        return self.repository.record_answer(user=user, data=data)

    def record_feedback(self, *, user, data: dict) -> dict:
        return self.repository.record_feedback(user=user, data=data)

    def begin_feedback_retry(self, *, user, data: dict) -> dict:
        return self.repository.begin_feedback_retry(user=user, data=data)

    def finish(self, *, user, data: dict) -> dict:
        current, should_generate, attempt_id = self.repository.begin_finish(user=user, data=data)
        if not should_generate:
            return current
        payload = self.repository.summary_payload(user=user, session_id=data['id'])
        if self.model_gateway is None:
            return self.repository.complete_summary(
                user=user, session_id=data['id'], request_id=attempt_id,
                failure_code='MODEL_UNAVAILABLE',
            )
        try:
            result = self.model_gateway.generate(
                system=(
                    '你是面试练习总结助手。仅依据输入中的真实题目、回答和反馈，'
                    '返回 strengths、gaps、next_steps 三个纯文本数组，不生成分数。'
                ),
                payload=payload,
            )
        except TimeoutError:
            return self.repository.complete_summary(
                user=user, session_id=data['id'], request_id=attempt_id,
                failure_code='MODEL_TIMEOUT',
            )
        except ValueError:
            return self.repository.complete_summary(
                user=user, session_id=data['id'], request_id=attempt_id,
                failure_code='INVALID_MODEL_OUTPUT',
            )
        except Exception:
            return self.repository.complete_summary(
                user=user, session_id=data['id'], request_id=attempt_id,
                failure_code='MODEL_UNAVAILABLE',
            )
        validated = self._validate_summary(result)
        if validated is None:
            return self.repository.complete_summary(
                user=user, session_id=data['id'], request_id=attempt_id,
                failure_code='INVALID_MODEL_OUTPUT',
            )
        return self.repository.complete_summary(
            user=user, session_id=data['id'], request_id=attempt_id, result=validated,
        )

    @staticmethod
    def _validate_summary(result):
        if not isinstance(result, dict):
            return None
        validated = {}
        for field in ('strengths', 'gaps', 'next_steps'):
            values = result.get(field)
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                return None
            validated[field] = values
        return validated
