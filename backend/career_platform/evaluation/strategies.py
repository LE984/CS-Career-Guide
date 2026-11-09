"""评估用排序策略适配器。

排序算法本身复用 `career_platform.rag.retrieval.TextRetrievalStrategy`（成员4 的
纯内存文本基线），这里只负责把它的 `RankedQuestion` 结果压成 `RankingStrategy`
约定的 ID 列表，避免在评估模块复制一份检索实现。
"""
from ..rag.retrieval import TextRetrievalStrategy
from .datasets import load_corpus

# 对照组：沿用成员4 文本基线的默认权重（题干4/标签3/要点2/答案1）。
BASELINE_WEIGHTS = None
# 对照变体：题干权重降到与标签、要点同级，用于验证“重措辞”与“重要点”的差异。
BALANCED_WEIGHTS = {'question': 3.0, 'tags': 3.0, 'key_points': 3.0, 'reference_answer': 1.0}
DEFAULT_MIN_SCORE = 0.0


class TextRankingStrategy:
    """把文本检索基线包装成只返回排序 ID 的评估策略。"""

    def __init__(self, questions, *, field_weights=None, min_score=DEFAULT_MIN_SCORE):
        self._retrieval = TextRetrievalStrategy(
            questions, field_weights=field_weights, min_score=min_score)

    def rank(self, *, query, top_k):
        ranked = self._retrieval.retrieve(
            query=query, role='', topic='', difficulty='', top_k=top_k)
        return [item.question_id for item in ranked]


def build_default_strategies() -> tuple[dict, dict]:
    """返回（策略表，语料摘要）。语料快照在构造时读入，运行期不访问网络或数据库。"""
    corpus, summary = load_corpus()
    questions = corpus['questions']
    strategies = {
        'text-baseline': TextRankingStrategy(questions),
        'text-balanced': TextRankingStrategy(questions, field_weights=BALANCED_WEIGHTS),
    }
    return strategies, summary
