"""检索排序指标：只接受相关 ID 与排名 ID，不读取数据库、模型或索引。

Precision 的分母固定为 K（不足 K 的空位算未命中），与文档中的定义一致；
重复的预测 ID 只按首次出现计分，未知 ID 视为无关但保留在逐例结果中作诊断。
"""
from collections.abc import Iterable, Mapping

METRIC_KEYS = ('precision_at_k', 'recall_at_k', 'f1_at_k', 'hit_rate_at_k', 'mrr')


def unique_ids(values: Iterable[object]) -> list[str]:
    """稳定去重并统一成字符串，避免 UUID 与整数 ID 混用时重复计分。"""
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        key = str(value)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    return ordered


def ranking_metrics(*, relevant_ids: Iterable[object], predicted_ids: Iterable[object], k: int) -> dict:
    """单个 query 的指标；同一输入必须得到同一输出。"""
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError('k 必须是正整数')
    relevant = set(unique_ids(relevant_ids))
    predicted = unique_ids(predicted_ids)[:k]
    hits = sum(1 for question_id in predicted if question_id in relevant)
    precision = hits / k
    recall = hits / len(relevant) if relevant else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    hit_rate = 1.0 if hits else 0.0
    reciprocal_rank = 0.0
    for position, question_id in enumerate(predicted, start=1):
        if question_id in relevant:
            reciprocal_rank = 1.0 / position
            break
    return {
        'precision_at_k': precision,
        'recall_at_k': recall,
        'f1_at_k': f1,
        'hit_rate_at_k': hit_rate,
        'mrr': reciprocal_rank,
    }


def aggregate_metrics(samples: Iterable[Mapping[str, float]]) -> dict:
    """对一个 query 组做宏平均；空组返回五个 0，保持对外结构稳定。"""
    collected = [dict(sample) for sample in samples]
    if not collected:
        return {key: 0.0 for key in METRIC_KEYS}
    return {key: sum(sample[key] for sample in collected) / len(collected) for key in METRIC_KEYS}
