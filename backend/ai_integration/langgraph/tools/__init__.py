from langchain_core.tools import tool
from .time_tool import get_time

try:
    from .keyword_search import keyword_search
except Exception as exc:
    keyword_search = None
    _keyword_error = exc

try:
    from .semantic_search import semantic_search
except Exception as exc:
    semantic_search = None
    _semantic_error = exc

try:
    from .read_chunk import read_chunk
except Exception as exc:
    read_chunk = None
    _read_chunk_error = exc


def _empty_tool_result(name, query, error):
    return {
        'success': False,
        'tool_name': name,
        'query': query,
        'error': str(error),
        'count': 0,
        'results': [],
    }


@tool
def keyword_search_tool(query: str, threshold: float = 0.7, top_k: int = 5) -> dict:
    """根据关键词搜索职业推荐记录。"""
    if keyword_search is None:
        return _empty_tool_result('keyword_search', query, _keyword_error)
    return keyword_search(query, threshold, top_k)


@tool
def semantic_search_tool(query: str, threshold: float = 0.5, top_k: int = 5) -> dict:
    """根据语义相似度搜索职业推荐记录。"""
    if semantic_search is None:
        return _empty_tool_result('semantic_search', query, _semantic_error)
    return semantic_search(query, threshold, top_k)


@tool
def read_chunk_tool(chunk_id: str) -> dict:
    """根据 ID 读取完整的职业推荐记录。"""
    if read_chunk is None:
        return {
            'success': False,
            'tool_name': 'read_chunk',
            'chunk_id': chunk_id,
            'error': str(_read_chunk_error),
        }
    return read_chunk(chunk_id)


__all__ = ['get_time', 'keyword_search_tool', 'semantic_search_tool', 'read_chunk_tool']