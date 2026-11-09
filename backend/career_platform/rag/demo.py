"""独立演示材料和检索入口；不是测试 fixture，也不是正式人审题库。"""

from dataclasses import asdict

from .retrieval import TextRetrievalStrategy


def _question(number, question, key_points, *, topic='集合', difficulty='easy',
              role='Java后端', permission_status='allowed', tags=()):
    return {
        'id': f'de000000-0000-4000-8000-{number:012d}',
        'category': '技术基础', 'role': role, 'topic': topic, 'difficulty': difficulty,
        'question': question, 'key_points': list(key_points),
        'reference_answer': '；'.join(key_points), 'tags': list(tags),
        'source': '文本检索演示自编虚构题，仅供观察检索行为，非正式题库',
        'source_url': '', 'permission_status': permission_status,
        'is_demo': True, 'collected_at': None,
    }


# 这些材料专门为用户授权的网页演示编写，不从 tests 导入或写入数据库。
DEMO_QUESTIONS = (
    _question(1, 'Java 集合中，List 与 Set 在顺序和重复元素上有什么区别？',
              ('List 通常保留元素顺序并允许重复', 'Set 不保留重复元素'), tags=('集合', 'List', 'Set')),
    _question(2, '为什么 ArrayList 适合按下标读取集合元素？',
              ('ArrayList 以数组保存元素', '按下标访问通常为常数时间', '中间插入或删除可能移动后续元素'),
              tags=('集合', 'ArrayList', '随机访问')),
    _question(3, '遍历 Java 集合时，Iterator 的基本作用是什么？',
              ('使用 hasNext 判断是否还有元素', '使用 next 读取下一个元素'), tags=('集合', 'Iterator', '遍历')),
    _question(4, 'HashMap 集合为什么需要同时考虑 hashCode 和 equals？',
              ('hashCode 帮助定位候选位置', 'equals 判断键是否相等', '相等对象应有相同 hashCode'),
              difficulty='medium', tags=('集合', 'HashMap', 'hashCode')),
    _question(5, 'Java 中 synchronized 用于解决什么问题？',
              ('保护共享状态的互斥访问', '同一监视器上的同步提供可见性保证'),
              topic='并发', tags=('并发', 'synchronized')),
    _question(6, '数据库索引为什么能减少查找时扫描的数据？',
              ('索引维护可用于定位记录的数据结构', '索引会增加存储和更新成本'),
              topic='数据库', tags=('索引', '数据库')),
    _question(7, 'Python 列表和集合在重复元素上有什么区别？',
              ('list 可以保存重复元素', 'set 保存不重复的元素'), role='Python后端', tags=('集合', 'list', 'set')),
    _question(8, '待审核演示题：ArrayList 集合的基础用途是什么？',
              ('此候选用于观察 pending 过滤，不会作为结果返回',), permission_status='pending', tags=('集合', 'ArrayList')),
    _question(9, '受限演示题：如何遍历集合？',
              ('此候选用于观察 restricted 过滤，不会作为结果返回',), permission_status='restricted', tags=('集合', '遍历')),
)


def retrieve_demo(data):
    """实际运行文本策略；演示响应始终显式标记，不能用于会话下发。"""
    results = TextRetrievalStrategy(DEMO_QUESTIONS).retrieve(**data)
    return {
        'is_demo': True,
        'dataset': 'text-retrieval-demo-v1',
        'count': len(results),
        'results': [dict(asdict(result), is_demo=True) for result in results],
        'message': '仅供检索演示；题目为自编虚构材料，不保存练习记录。',
    }
