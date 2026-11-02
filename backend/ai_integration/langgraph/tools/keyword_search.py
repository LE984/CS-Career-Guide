#!/usr/bin/env python3
"""
关键词搜索工具

基于 jieba 分词的精确关键词匹配，使用 SQLAlchemy 连接池管理数据库连接
"""

import os
import sys
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Django 设置
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cs_career_guide.settings')
django.setup()

# 导入 SQLAlchemy 用于连接池管理
try:
    from sqlalchemy import create_engine, text, URL
    from sqlalchemy.pool import QueuePool
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("SQLAlchemy not available, using Django ORM instead")

from ai_integration.arag_integration import ARAGCareerSearch
from django.conf import settings

# ==================== 连接池配置 ====================
# Normalize the default database so SQLite demo mode never requires MySQL keys.
_db_settings = settings.DATABASES['default']
_db_engine = str(_db_settings.get('ENGINE', '')).lower()
_db_is_mysql = _db_engine.endswith('.mysql')
_db_user = _db_settings.get('USER', '')
_db_password = _db_settings.get('PASSWORD', '')
_db_host = _db_settings.get('HOST', '')
_db_port = _db_settings.get('PORT') or '3306'
_db_name = _db_settings.get('NAME', '')
_db_charset = _db_settings.get('OPTIONS', {}).get('charset', 'utf8mb4')
POOL_CONFIG = {
    'max_connections': getattr(settings, 'DATABASE_MAX_OVERFLOW', 20),
    'min_connections': getattr(settings, 'DATABASE_POOL_SIZE', 5),
    'idle_timeout': 300,
    'pool_timeout': getattr(settings, 'DATABASE_POOL_TIMEOUT', 30),
    'recycle': getattr(settings, 'DATABASE_POOL_RECYCLE', 3600),
}


# ==================== 全局连接池实例 ====================
# 整个应用只会初始化一次，多个工具函数共享
_connection_pool = None
_pool_lock = __import__('threading').Lock()

def get_connection_pool():
    """获取数据库连接池（单例模式）"""
    global _connection_pool
    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None and SQLALCHEMY_AVAILABLE and globals().get("_db_is_mysql", True):
                try:
                    # 创建 MySQL 连接字符串
                    db_url = URL.create(
                        'mysql+pymysql',
                        username=_db_user,
                        password=_db_password,
                        host=_db_host,
                        port=int(_db_port),
                        database=_db_name,
                        query={'charset': _db_charset},
                    )
                    # 创建连接池
                    _connection_pool = create_engine(
                        db_url,
                        poolclass=QueuePool,
                        max_overflow=POOL_CONFIG['max_connections'],
                        pool_size=POOL_CONFIG['min_connections'],
                        pool_timeout=POOL_CONFIG['pool_timeout'],
                        pool_recycle=POOL_CONFIG['recycle'],
                        echo=False  # 设置为 True 可开启 SQL 日志
                    )
                    logger.info(f"Database connection pool initialized successfully. "
                                f"Max connections: {POOL_CONFIG['max_connections']}, "
                                f"Min connections: {POOL_CONFIG['min_connections']}")
                except Exception as e:
                    logger.error(f"Failed to initialize connection pool: {str(e)}")
                    _connection_pool = None
    return _connection_pool

def execute_query(sql: str, params: dict = None) -> list:
    """
    使用连接池执行 SQL 查询
    
    Args:
        sql: SQL 查询语句
        params: 查询参数（字典形式）
        
    Returns:
        查询结果列表，每个元素是字典
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.warning("SQLAlchemy not available, returning empty result")
        return []
    
    pool = get_connection_pool()
    if not pool:
        logger.error("Connection pool not available")
        return []
    
    try:
        with pool.connect() as conn:
            result = conn.execute(text(sql), params or {})
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result]
    except Exception as e:
        logger.error(f"Database query error: {str(e)}")
        return []

# ==================== 搜索器实例 ====================
_search_instance = None

def get_search_instance() -> ARAGCareerSearch:
    """获取搜索器实例（单例模式）"""
    global _search_instance
    if _search_instance is None:
        _search_instance = ARAGCareerSearch()
    return _search_instance

# ==================== 关键词搜索函数 ====================
def keyword_search(
    query: str,
    threshold: float = 0.001,
    top_k: int = 5
) -> dict:
    """
    关键词搜索工具 - 使用 MySQL 全文索引进行高效关键词匹配
    
    Args:
        query: 搜索查询字符串
        threshold: 匹配度阈值（0-1）
        top_k: 返回的最大结果数
        
    Returns:
        包含搜索结果的字典
    """
    try:
        # 优先使用连接池进行 MySQL 全文索引搜索
        if SQLALCHEMY_AVAILABLE and globals().get("_db_is_mysql", True) and get_connection_pool():
            return _keyword_search_with_pool(query, threshold, top_k)
        else:
            # 回退到 ARAG 搜索器
            search = get_search_instance()
            results = search.keyword_search(query, threshold=threshold, top_k=top_k)
            return _format_results(results, query)
            
    except Exception as e:
        logger.error(f"Keyword search error: {str(e)}")
        return {
            "success": False,
            "tool_name": "keyword_search",
            "query": query,
            "error": str(e),
            "results": []
        }

def _keyword_search_with_pool(query: str, threshold: float, top_k: int) -> dict:
    """
    使用连接池执行 MySQL 全文索引搜索
    
    使用 MATCH...AGAINST 语法进行全文搜索，同时搜索 self_introduction 和 introduction_preview 字段
    """
    # 使用 MySQL 全文索引查询 - 同时搜索两个字段
    sql = """
        SELECT 
            id,
            self_introduction,
            introduction_preview,
            recommendations,
            MATCH(self_introduction, introduction_preview) AGAINST(:query IN NATURAL LANGUAGE MODE) AS match_score
        FROM ai_integration_careerrecommendationrecord
        WHERE MATCH(self_introduction, introduction_preview) AGAINST(:query IN NATURAL LANGUAGE MODE)
        HAVING match_score >= :threshold
        ORDER BY match_score DESC
        LIMIT :top_k
    """
    
    params = {
        'query': query,
        'threshold': threshold,
        'top_k': top_k
    }
    
    results = execute_query(sql, params)
    
    # 如果当前索引不支持多字段搜索，回退到单字段搜索
    if not results:
        logger.info("Multi-field search returned no results, falling back to single field")
        return _keyword_search_single_field(query, threshold, top_k)
    
    return _format_results(results, query)

def _keyword_search_single_field(query: str, threshold: float, top_k: int) -> dict:
    """
    单字段全文搜索（回退方案）- 使用多字段索引作为回退
    """
    # 使用多字段索引作为回退（因为单字段索引已删除）
    sql = """
        SELECT 
            id,
            self_introduction,
            introduction_preview,
            recommendations,
            MATCH(self_introduction, introduction_preview) AGAINST(:query IN NATURAL LANGUAGE MODE) AS match_score
        FROM ai_integration_careerrecommendationrecord
        WHERE MATCH(self_introduction, introduction_preview) AGAINST(:query IN NATURAL LANGUAGE MODE)
        HAVING match_score >= :threshold
        ORDER BY match_score DESC
        LIMIT :top_k
    """
    
    params = {
        'query': query,
        'threshold': threshold,
        'top_k': top_k
    }
    
    results = execute_query(sql, params)
    return _format_results(results, query)

def _format_results(results: list, query: str) -> dict:
    """格式化搜索结果"""
    formatted_results = []
    for r in results:
        recommendations = []
        if r.get("recommendations"):
            try:
                recommendations = json.loads(r.get("recommendations", "[]"))[:3]
            except:
                pass
        
        formatted_results.append({
            "id": r.get("id"),
            "preview": r.get("introduction_preview", r.get("self_introduction", ""))[:100],
            "match_score": r.get("match_score", 0),
            "match_type": "keyword",
            "recommendations": recommendations
        })
    
    return {
        "success": True,
        "tool_name": "keyword_search",
        "query": query,
        "count": len(formatted_results),
        "results": formatted_results
    }

# 工具元数据
TOOL_METADATA = {
    "name": "keyword_search",
    "description": "根据关键词搜索职业推荐记录（使用MySQL全文索引）",
    "parameters": {
        "query": {"type": "string", "description": "搜索查询词", "required": True},
        "threshold": {"type": "number", "description": "匹配度阈值（0-1）", "default": 0.7},
        "top_k": {"type": "integer", "description": "返回最大结果数", "default": 5}
    }
}

if __name__ == "__main__":
    # 测试连接池
    logger.info("Testing connection pool initialization...")
    pool = get_connection_pool()
    if pool:
        logger.info("Connection pool initialized successfully")
    
    # 测试搜索
    result = keyword_search("Python 数据分析")
    print(f"关键词搜索结果: {result['count']} 条")
    for r in result["results"]:
        print(f"  - {r['preview']} (匹配度: {r['match_score']:.2f})")
