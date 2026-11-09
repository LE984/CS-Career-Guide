"""成员四的编排入口；独立演示可用，正式检索与逐题反馈仍未实现。"""
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
        """预览候选题；实现后调用 RetrievalStrategy 并返回来源证据。"""
        # TODO(成员4)：TextRetrievalStrategy 已完成离线检索，正式数据就绪后接本入口。
        # 1. 规范化岗位/JD、知识点、难度、top_k；许可与条件过滤不能遗漏。
        # 2. 调用 self.retriever.retrieve，组装 RankedQuestion 和真实引用来源。
        # 3. 区分“真实无命中”和“检索未实现/不可用”；不能用空列表冒充成功。
        # 本入口仅预览，不创建会话，也不把候选题标记为已下发。
        raise FeatureNotImplemented(self.module, 'retrieve')

    def answer(self, *, user, data: dict) -> dict:
        """预留逐题反馈编排；待检索基线及成员五的保存接口就绪后实现。"""
        # TODO(成员4)：校验会话归属、active 状态及题目已下发关系。
        # 通过 self.records.record_answer 先保存真实回答和题目快照，
        # 再调用 self.model_gateway.generate，校验 answer_quote 和 evidence，
        # 最后通过 self.records.record_feedback 保存反馈；不直接建历史表。
        # 模型失败仍须保留回答；request_id 重试不能重复保存或调用模型。
        raise FeatureNotImplemented(self.module, 'answer')
