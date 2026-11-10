"""成员四的编排入口；检索支持依赖注入，生产题库和逐题反馈待接入。"""
from dataclasses import asdict

from ..composition_base import UnavailableService
from ..errors import FeatureNotImplemented

class InterviewRagService(UnavailableService):
    def __init__(self, *, retriever=None, model_gateway=None, records=None):
        super().__init__('rag')
        self.retriever = retriever
        self.model_gateway = model_gateway
        self.records = records

    def demo_retrieve(self, *, user, data: dict) -> dict:
        """用户显式选择的只读演示；不下发题目、不访问正式题库或记录。"""
        from .demo import retrieve_demo
        return retrieve_demo(data)

    def retrieve(self, *, user, data: dict) -> dict:
        """只读预览；data 由 HTTP 序列化器校验，候选许可由可信检索适配器筛选。"""
        if self.retriever is None:
            raise FeatureNotImplemented(self.module, 'retrieve')
        # 尚无岗位目录依赖，不能静默忽略 job_id 或冒称核验过岗位。
        if data.get('job_id') is not None:
            raise FeatureNotImplemented(self.module, 'retrieve_by_job')
        role = data['role'].strip()
        topic = data.get('topic', '').strip()
        jd_text = data.get('jd_text', '').strip()
        # JD 优先作为自由文本；无 JD 时按知识点检索，无知识点则使用岗位。
        query = jd_text or topic or role
        rows = self.retriever.retrieve(
            query=query, role=role, topic=topic,
            difficulty=data.get('difficulty', 'easy'), top_k=data.get('top_k', 5),
        )
        results = [dict(
            question_id=row.question_id, question=row.question,
            key_points=list(row.key_points),
            evidence=[asdict(item) for item in row.evidence],
            score=row.score, origin=row.origin,
        ) for row in rows]
        return {
            'count': len(results), 'results': results,
            'message': '' if results else '没有符合当前条件及相关性要求的题目，请调整条件。',
        }

    def answer(self, *, user, data: dict) -> dict:
        """预留逐题反馈编排；待检索基线及成员五的保存接口就绪后实现。"""
        # TODO(成员4)：校验会话归属、active 状态及题目已下发关系。
        # 通过 self.records.record_answer 先保存真实回答和题目快照，
        # 再调用 self.model_gateway.generate，校验 answer_quote 和 evidence，
        # 最后通过 self.records.record_feedback 保存反馈；不直接建历史表。
        # 模型失败仍须保留回答；request_id 重试不能重复保存或调用模型。
        raise FeatureNotImplemented(self.module, 'answer')
