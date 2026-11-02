"""
A-RAG集成模块 - 提供高级搜索和缓存功能
"""

import os
import json
import time
import hashlib
import threading
from typing import List, Dict, Any, Optional
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

try:
    import lancedb
    import pyarrow as pa
    import numpy as np
    VECTOR_IMPORT_ERROR = None
except ImportError as exc:
    lancedb = None
    pa = None
    np = None
    VECTOR_IMPORT_ERROR = exc
    import logging
    logging.getLogger(__name__).warning(
        'LanceDB/PyArrow/NumPy unavailable; semantic search will return empty results: %s', exc
    )

from django.conf import settings
from django.core.cache import cache
from cs_career_guide.vector_store import (
    CAREER_TABLE_NAME, career_schema, career_record, open_career_table,
    validate_embedding, validate_model_dimension,
)

import logging
logger = logging.getLogger(__name__)


class ARAGCareerSearch:
    """基于A-RAG的职业推荐搜索类"""
    
    def __init__(self, db_path: str = None):
        """
        初始化搜索器
        
        Args:
            db_path: LanceDB数据库路径
        """
        if db_path is None:
            db_path = str(settings.LANCEDB_PATH)

        if lancedb is None:
            raise ImportError(f'LanceDB dependencies are unavailable: {VECTOR_IMPORT_ERROR}')

        self.db_path = db_path
        self.db = lancedb.connect(db_path)
        self.table_name = CAREER_TABLE_NAME
        self.table = open_career_table(self.db, settings.EMBEDDING_DIMENSION)
        
        # 初始化缓存
        self._cache = {}
        self._cache_lock = threading.Lock()
        
        # 初始化线程池
        self._executor = ThreadPoolExecutor(max_workers=settings.SEARCH_MAX_WORKERS)
        
        # 模型缓存
        self._model = None
        self._model_lock = threading.Lock()
        
        logger.info(f"ARAGCareerSearch initialized with db_path: {db_path}")
    
    def _create_table(self):
        """创建LanceDB表"""
        schema = career_schema(settings.EMBEDDING_DIMENSION)
        self.db.create_table(self.table_name, schema=schema)
        logger.info(f"Created LanceDB table: {self.table_name}")
    
    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _tokenize_chinese(self, text: str) -> list:
        """
        中文分词 - 支持中英文混合文本
        
        Args:
            text: 待分词的文本
            
        Returns:
            分词结果列表
        """
        try:
            # 尝试使用 jieba 分词
            import jieba
            # 兼容不同版本的 jieba（jieba vs jieba3k）
            try:
                # 新版本 jieba
                if hasattr(jieba, 'lcut'):
                    words = jieba.lcut(text.lower())
                else:
                    # 旧版本 jieba3k
                    words = list(jieba.cut(text.lower()))
            except AttributeError as e:
                if "ImpImporter" in str(e):
                    logger.warning("jieba compatibility issue, using fallback tokenization")
                    return self._simple_tokenize(text)
                raise
            # 过滤空字符串和单个字符（除了英文字母）
            return [w for w in words if len(w) > 1 or w.isalpha()]
        except ImportError:
            # 如果没有 jieba，使用备选方案
            logger.warning("jieba not available, using fallback tokenization")
            return self._simple_tokenize(text)
        except Exception as e:
            # 其他 jieba 错误，回退到备选方案
            logger.warning(f"jieba tokenization failed: {str(e)}, using fallback")
            return self._simple_tokenize(text)
    
    def _simple_tokenize(self, text: str) -> list:
        """
        简单分词备选方案 - 使用字符级匹配和英文单词分割
        
        Args:
            text: 待分词的文本
            
        Returns:
            分词结果列表
        """
        result = []
        current_word = ""
        
        for char in text.lower():
            if char.isalpha():
                # 英文字母，继续累积
                current_word += char
            else:
                # 非英文字母
                if current_word:
                    result.append(current_word)
                    current_word = ""
                # 添加中文字符作为单独的词
                if char.strip():
                    result.append(char)
        
        # 处理最后一个英文单词
        if current_word:
            result.append(current_word)
        
        # 添加基于空格和标点分割的短语（提高匹配率）
        text_lower = text.lower()
        import re
        # 按空格、标点分割
        phrases = re.split(r'[\s，。！？、；：,.!?;:]', text_lower)
        for phrase in phrases:
            if phrase.strip() and len(phrase) > 1:
                result.append(phrase.strip())
        
        # 添加2-4字符的中文短语
        for i in range(len(text_lower)):
            for length in range(2, min(5, len(text_lower) - i + 1)):
                substr = text_lower[i:i+length]
                # 只添加全中文或全英文的短语
                if all(c.isalpha() for c in substr) or all(not c.isalpha() for c in substr if c.strip()):
                    result.append(substr)
        
        return list(set(result))  # 去重
    
    def keyword_search(
        self, 
        query: str, 
        threshold: float = 0.7,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        关键词搜索 - 搜索完整的 self_introduction 字段
        
        Args:
            query: 搜索查询
            threshold: 匹配度阈值
            top_k: 返回的最大结果数
            
        Returns:
            匹配的推荐记录列表，包含 recommendations 和 analysis_result
        """
        start_time = time.time()
        
        try:
            # 获取所有记录（限制数量，避免处理过多数据）
            results = self.table.to_pandas().to_dict('records')
            
            logger.info(f"Keyword search: found {len(results)} total records")
            
            # 使用中文分词
            query_words = set(self._tokenize_chinese(query))
            if not query_words:
                return []
            
            logger.info(f"Query tokens: {query_words}")
            
            scored_results = []
            for result in results:
                # 搜索完整的 self_introduction 字段
                content = result.get("self_introduction", "")
                # 确保 content 是字符串类型（修复 float 类型错误）
                if not isinstance(content, str):
                    content = str(content) if content else ""
                
                record_words = set(self._tokenize_chinese(content))
                common_words = query_words.intersection(record_words)
                
                if common_words:
                    match_score = len(common_words) / len(query_words)
                    if match_score >= threshold:
                        # 返回完整的记录信息，包括 recommendations 和 analysis_result
                        scored_results.append({
                            "id": result.get("id"),
                            "user_id": result.get("user_id"),
                            "self_introduction": content,
                            "introduction_preview": result.get("introduction_preview", ""),
                            "recommendations": result.get("recommendations", []),
                            "analysis_result": result.get("analysis_result", ""),
                            "match_score": match_score,
                            "match_type": "keyword"
                        })
                        logger.debug(f"Match found: {common_words}, score: {match_score}")
            
            # 按匹配度排序
            scored_results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            
            search_time = time.time() - start_time
            logger.info(f"Keyword search completed in {search_time:.2f}s, found {len(scored_results)} matches")
            
            return scored_results[:top_k]
            
        except Exception as e:
            logger.error(f"Keyword search error: {str(e)}")
            return []
    
    def _get_model(self):
        """
        懒加载模型，提高性能
        """
        if not settings.EMBEDDING_ENABLED:
            return None
        with self._model_lock:
            if self._model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    model_id = settings.EMBEDDING_MODEL
                    model_cache_name = f"models--{model_id.replace('/', '--')}"
                    local_model_paths = []
                    if settings.EMBEDDING_MODEL_PATH:
                        local_model_paths.append(
                            os.path.expandvars(os.path.expanduser(settings.EMBEDDING_MODEL_PATH))
                        )
                        if not os.path.isabs(local_model_paths[0]):
                            local_model_paths[0] = str(settings.BASE_DIR / local_model_paths[0])
                    local_model_paths.extend([
                        str(settings.BASE_DIR.parent / "~" / ".cache" / "huggingface" / "hub" / model_cache_name),
                        os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub", model_cache_name),
                        os.path.join(os.path.expanduser("~"), ".cache", "torch", "sentence_transformers", model_id.replace("/", "_")),
                    ])
                    
                    self._model = None
                    for local_path in local_model_paths:
                        if os.path.exists(local_path):
                            try:
                                self._model = SentenceTransformer(
                                    local_path,
                                    device=settings.EMBEDDING_DEVICE,
                                    local_files_only=True,
                                )
                                validate_model_dimension(self._model, settings.EMBEDDING_DIMENSION)
                                logger.info(f"Model loaded from local cache: {local_path}")
                                break
                            except Exception as e:
                                logger.warning(f"Failed to load from {local_path}: {str(e)}")
                                self._model = None
                    
                    # 优先使用 Hub 缓存；仅在允许时联网下载。
                    if self._model is None:
                        try:
                            self._model = SentenceTransformer(
                                model_id,
                                device=settings.EMBEDDING_DEVICE,
                                local_files_only=not settings.EMBEDDING_ALLOW_DOWNLOAD,
                            )
                            validate_model_dimension(self._model, settings.EMBEDDING_DIMENSION)
                            logger.info(f"Embedding model loaded: {model_id}")
                        except Exception as e:
                            logger.warning(f"Failed to load embedding model: {str(e)}")
                            self._model = None
                            
                except ImportError:
                    logger.warning("sentence_transformers not installed, cannot load model")
                    self._model = None
                except Exception as e:
                    logger.warning(f"Model loading failed: {str(e)}")
                    self._model = None
            return self._model
    
    def semantic_search(
        self, 
        query: str, 
        threshold: float = 0.5,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        语义搜索 - 优先搜索高亮块（introduction_preview），如果没有则搜索完整的 self_introduction
        
        Args:
            query: 搜索查询
            threshold: 相似度阈值
            top_k: 返回的最大结果数
            
        Returns:
            匹配的推荐记录列表，包含 recommendations 和 analysis_result
        """
        start_time = time.time()
        
        try:
            # 快速检查模型是否可用
            model = self._get_model()
            if model is None:
                logger.warning("Model not available, falling back to keyword search")
                return self.keyword_search(query, threshold=threshold, top_k=top_k)
            
            # 获取所有记录
            results = self.table.to_pandas().to_dict('records')
            
            if not results:
                return []
            
            # 生成查询向量
            query_embedding = np.asarray(validate_embedding(
                model.encode([query], normalize_embeddings=True)[0],
                settings.EMBEDDING_DIMENSION,
            ))
            
            # 计算相似度
            scored_results = []
            for result in results:
                # 优先使用高亮块，没有则使用完整自我介绍
                preview = result.get("introduction_preview", "")
                
                # 如果有高亮块，使用高亮块搜索
                if preview and isinstance(preview, str) and len(preview.strip()) > 0:
                    content = preview
                else:
                    # 如果没有高亮块，使用完整的 self_introduction
                    content = result.get("self_introduction", "")
                
                # 确保 content 是字符串类型（修复 float 类型错误）
                if not isinstance(content, str):
                    content = str(content) if content else ""
                
                # 如果内容为空，跳过
                if not content or len(content.strip()) == 0:
                    continue
                
                # 生成embedding
                record_embedding = model.encode(
                    [content], 
                    normalize_embeddings=True
                )[0]
                record_embedding = validate_embedding(record_embedding, settings.EMBEDDING_DIMENSION)
                
                # 计算余弦相似度
                similarity = np.dot(query_embedding, record_embedding)
                
                if similarity >= threshold:
                    # 返回完整的记录信息，包括 recommendations 和 analysis_result
                    scored_results.append({
                        "id": result.get("id"),
                        "user_id": result.get("user_id"),
                        "self_introduction": result.get("self_introduction", ""),
                        "introduction_preview": preview,
                        "recommendations": result.get("recommendations", []),
                        "analysis_result": result.get("analysis_result", ""),
                        "match_score": float(similarity),
                        "match_type": "semantic"
                    })
            
            # 按相似度排序
            scored_results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            
            search_time = time.time() - start_time
            logger.info(f"Semantic search completed in {search_time:.2f}s, found {len(scored_results)} matches")
            
            return scored_results[:top_k]
            
        except Exception as e:
            logger.error(f"Semantic search error: {str(e)}, falling back to keyword search")
            return self.keyword_search(query, threshold=threshold, top_k=top_k)
    
    def hybrid_search(
        self, 
        query: str, 
        keyword_threshold: float = 0.7,
        semantic_threshold: float = 0.8,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        混合搜索 - 结合关键词和语义搜索
        
        Args:
            query: 搜索查询
            keyword_threshold: 关键词匹配度阈值
            semantic_threshold: 语义相似度阈值
            top_k: 返回的最大结果数
            
        Returns:
            匹配的推荐记录列表
        """
        start_time = time.time()
        
        # 先执行关键词搜索（更可靠）
        keyword_results = self.keyword_search(
            query, 
            keyword_threshold, 
            top_k
        )
        
        # 尝试执行语义搜索，但设置超时
        semantic_results = []
        try:
            import threading
            
            def semantic_search_wrapper():
                nonlocal semantic_results
                semantic_results = self.semantic_search(
                    query, 
                    semantic_threshold, 
                    top_k
                )
            
            # 创建线程执行语义搜索
            semantic_thread = threading.Thread(target=semantic_search_wrapper)
            semantic_thread.daemon = True
            semantic_thread.start()
            
            # 等待语义搜索完成，最多等待5秒
            semantic_thread.join(timeout=5)
            
            # 如果线程还在运行，说明超时了
            if semantic_thread.is_alive():
                logger.warning("Semantic search timed out")
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
        
        # 合并结果
        seen_ids = set()
        merged_results = []
        
        # 优先添加语义搜索结果（通常更准确）
        for result in semantic_results:
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                merged_results.append(result)
        
        # 添加关键词搜索结果
        for result in keyword_results:
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                merged_results.append(result)
        
        # 按匹配度排序
        merged_results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        search_time = time.time() - start_time
        logger.info(f"Hybrid search completed in {search_time:.2f}s, found {len(merged_results)} matches")
        
        return merged_results[:top_k]
    
    def get_cached_result(self, query: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的搜索结果
        
        Args:
            query: 搜索查询
            
        Returns:
            缓存的结果或None
        """
        cache_key = self._get_cache_key(query)
        
        # 先检查内存缓存
        with self._cache_lock:
            if cache_key in self._cache:
                cached_data = self._cache[cache_key]
                # 检查是否过期（1小时）
                if time.time() - cached_data["timestamp"] < 3600:
                    logger.info(f"Cache hit for query: {query[:50]}...")
                    return cached_data["result"]
        
        # 再检查Django缓存
        cached_result = cache.get(f"career_search_{cache_key}")
        if cached_result:
            logger.info(f"Django cache hit for query: {query[:50]}...")
            return cached_result
        
        return None
    
    def set_cached_result(self, query: str, result: Dict[str, Any]):
        """
        设置缓存结果
        
        Args:
            query: 搜索查询
            result: 搜索结果
        """
        cache_key = self._get_cache_key(query)
        
        # 保存到内存缓存
        with self._cache_lock:
            self._cache[cache_key] = {
                "result": result,
                "timestamp": time.time()
            }
        
        # 保存到Django缓存（1小时过期）
        cache.set(f"career_search_{cache_key}", result, 3600)
        
        logger.info(f"Cached result for query: {query[:50]}...")
    
    def search_with_cache(
        self, 
        query: str,
        use_cache: bool = True,
        **search_kwargs
    ) -> List[Dict[str, Any]]:
        """
        带缓存的搜索
        
        Args:
            query: 搜索查询
            use_cache: 是否使用缓存
            **search_kwargs: 传递给hybrid_search的参数
            
        Returns:
            搜索结果列表
        """
        if use_cache:
            cached = self.get_cached_result(query)
            if cached:
                return cached
        
        # 执行搜索
        results = self.hybrid_search(query, **search_kwargs)
        
        # 缓存结果
        if use_cache and results:
            self.set_cached_result(query, results)
        
        return results
    
    def add_record(self, record_data: Dict[str, Any], *, upsert=False):
        """
        添加记录到LanceDB
        
        Args:
            record_data: 记录数据
        """
        try:
            # 没有可用模型时保留文本，embedding 为空，等待真实模型重算。
            record_data = dict(record_data)
            record_data["embedding"] = None
            try:
                model = self._get_model()
                if model:
                    embedding = model.encode(
                        [record_data["self_introduction"]], 
                        normalize_embeddings=True
                    )[0].tolist()
                    record_data["embedding"] = validate_embedding(embedding, settings.EMBEDDING_DIMENSION)
            except Exception as e:
                logger.error(f"Error generating embedding: {str(e)}")
                record_data["embedding"] = None
            
            # 添加记录
            rows = [career_record(record_data, settings.EMBEDDING_DIMENSION)]
            # Explicit Arrow types are required when an entire batch has null vectors.
            typed_rows = pa.Table.from_pylist(rows, schema=career_schema(settings.EMBEDDING_DIMENSION))
            if upsert:
                self.table.merge_insert("id").when_matched_update_all().when_not_matched_insert_all().execute(typed_rows)
            else:
                self.table.add(typed_rows)
            logger.info(f"Added record {record_data['id']} to LanceDB")
            return True
            
        except Exception as e:
            logger.error(f"Error adding record to LanceDB: {str(e)}")
            return False
    
    def read_chunk(self, record_id: str) -> Dict[str, Any]:
        """
        Chunk Read - 根据ID读取完整的推荐记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            完整的推荐记录，包含所有字段
        """
        try:
            start_time = time.time()
            
            # 从LanceDB中读取记录
            results = self.table.to_pandas().to_dict('records')
            
            # 查找指定ID的记录
            for result in results:
                if str(result.get('id')) == str(record_id):
                    read_time = time.time() - start_time
                    logger.info(f"Chunk read completed in {read_time:.2f}s for record {record_id}")
                    
                    # 解析recommendations字段（如果是JSON字符串）
                    if isinstance(result.get('recommendations'), str):
                        try:
                            result['recommendations'] = json.loads(result['recommendations'])
                        except:
                            pass
                    
                    return {
                        "success": True,
                        "record": result,
                        "read_time": read_time
                    }
            
            # 如果在LanceDB中没找到，尝试从Django数据库中读取
            try:
                from ai_integration.models import CareerRecommendationRecord
                record = CareerRecommendationRecord.objects.get(id=record_id)
                
                result = {
                    "id": str(record.id),
                    "user_id": str(record.user.id) if record.user else "",
                    "self_introduction": record.self_introduction,
                    "recommendations": record.recommendations,
                    "analysis_result": record.analysis_result or "",
                    "created_at": record.created_at.isoformat()
                }
                
                read_time = time.time() - start_time
                logger.info(f"Chunk read from Django DB in {read_time:.2f}s for record {record_id}")
                
                return {
                    "success": True,
                    "record": result,
                    "read_time": read_time,
                    "source": "django_db"
                }
                
            except Exception as db_error:
                logger.warning(f"Record {record_id} not found in Django DB: {str(db_error)}")
            
            logger.warning(f"Record {record_id} not found")
            return {
                "success": False,
                "error": f"Record {record_id} not found"
            }
            
        except Exception as e:
            logger.error(f"Error reading chunk {record_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def read_chunks(self, record_ids: List[str]) -> Dict[str, Any]:
        """
        批量Chunk Read - 根据多个ID读取完整的推荐记录
        
        Args:
            record_ids: 记录ID列表
            
        Returns:
            包含所有记录的字典
        """
        try:
            start_time = time.time()
            
            results = []
            errors = []
            
            for record_id in record_ids:
                result = self.read_chunk(record_id)
                if result.get("success"):
                    results.append(result.get("record"))
                else:
                    errors.append({
                        "id": record_id,
                        "error": result.get("error")
                    })
            
            read_time = time.time() - start_time
            logger.info(f"Batch chunk read completed in {read_time:.2f}s, {len(results)} success, {len(errors)} failed")
            
            return {
                "success": True,
                "records": results,
                "errors": errors,
                "read_time": read_time
            }
            
        except Exception as e:
            logger.error(f"Error in batch chunk read: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def close(self):
        """关闭资源"""
        self._executor.shutdown(wait=True)
        logger.info("ARAGCareerSearch closed")


# 全局搜索器实例
_career_search = None

class FallbackCareerSearch:
    """降级搜索器，当LanceDB不可用时使用"""
    
    def search_with_cache(self, query: str, **kwargs):
        """降级搜索，总是返回空结果"""
        logger.warning("Using fallback career search (LanceDB not available)")
        return []
    
    def read_chunks(self, record_ids: list):
        """降级读取，总是返回空结果"""
        return {
            "success": True,
            "records": [],
            "errors": [],
            "read_time": 0
        }

def get_career_search():
    """获取全局搜索器实例（单例模式）"""
    global _career_search
    if _career_search is None:
        import threading
        
        def create_search_instance():
            global _career_search
            try:
                _career_search = ARAGCareerSearch()
            except Exception as e:
                import traceback
                logger.error(f"Failed to create ARAGCareerSearch: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                # 使用降级搜索器
                _career_search = FallbackCareerSearch()
                logger.warning("Using fallback career search due to initialization failure")
        
        # 创建线程执行初始化
        init_thread = threading.Thread(target=create_search_instance)
        init_thread.daemon = True
        init_thread.start()
        
        # 等待初始化完成，最多等待2秒
        init_thread.join(timeout=2)
        
        # 如果线程还在运行，说明初始化超时了
        if init_thread.is_alive():
            logger.error("ARAGCareerSearch initialization timed out")
            # 使用降级搜索器
            _career_search = FallbackCareerSearch()
            logger.warning("Using fallback career search due to initialization timeout")
    return _career_search
