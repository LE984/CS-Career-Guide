"""
优化后的职业推荐视图 - 使用A-RAG、异步处理和缓存
"""

import os
import json
import time
import threading
import hashlib
from concurrent.futures import ThreadPoolExecutor
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from cs_career_guide.ai_config import get_llm_kwargs
from ai_integration.models import AIUsageRecord, CareerRecommendationRecord, SeniorAdvice
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
import logging

from ai_integration.langgraph.graphs.graph import create_chat_workflow
from .serializers import SeniorAdviceSerializer
from .senior_advice_views import senior_advice_list
from ai_integration.arag_integration import get_career_search
from ai_integration.arag_agent import get_arag_agent

logger = logging.getLogger(__name__)

# 全局线程池
_thread_pool = ThreadPoolExecutor(max_workers=settings.SEARCH_MAX_WORKERS)

# 内存缓存
_memory_cache = {}
_cache_lock = threading.Lock()


def _get_cache_key(text: str) -> str:
    """生成缓存键"""
    return hashlib.md5(text.encode()).hexdigest()


def _get_cached_result(query: str):
    """获取缓存结果"""
    cache_key = _get_cache_key(query)
    
    # 检查内存缓存
    with _cache_lock:
        if cache_key in _memory_cache:
            cached_data = _memory_cache[cache_key]
            if time.time() - cached_data["timestamp"] < 3600:  # 1小时过期
                logger.info(f"Memory cache hit for query: {query[:50]}...")
                return cached_data["result"]
    
    # 检查Django缓存
    cached_result = cache.get(f"career_search_{cache_key}")
    if cached_result:
        logger.info(f"Django cache hit for query: {query[:50]}...")
        return cached_result
    
    return None


def _set_cached_result(query: str, result):
    """设置缓存结果"""
    cache_key = _get_cache_key(query)
    
    # 保存到内存缓存
    with _cache_lock:
        _memory_cache[cache_key] = {
            "result": result,
            "timestamp": time.time()
        }
    
    # 保存到Django缓存
    cache.set(f"career_search_{cache_key}", result, 3600)


def _simple_llm_recommendation(self_introduction: str) -> dict:
    """
    简化版LLM推荐 - 直接调用大模型生成职业推荐，跳过复杂的LangGraph工作流
    """
    start_time = time.time()
    logger.info("Starting simple LLM recommendation generation")
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        # 获取环境变量
        api_key = settings.LLM_API_KEY
        base_url = settings.LLM_BASE_URL
        
        logger.info(f"API Key available: {bool(api_key)}")
        logger.info(f"Base URL: {base_url}")
        
        if not api_key or not base_url:
            raise ValueError("API key or base URL not configured")
        
        # 创建LLM实例
        llm = ChatOpenAI(
            temperature=0.7,
            **get_llm_kwargs(),
        )
        
        # 构建提示词（注意：JSON中的大括号需要转义为{{和}}）
        system_prompt = """你是一个专业的职业推荐顾问。请根据用户提供的自我介绍，分析其技能、背景和职业期望，推荐3个最适合的职业方向。

要求：
1. 推荐的职业必须是计算机相关领域的具体岗位
2. 每个推荐需要包含：职业名称、匹配度（0-100）、推荐理由
3. 匹配度要根据用户的技能与岗位需求的契合程度来确定
4. 理由要具体，结合用户的背景说明为什么适合这个职业

请以JSON格式输出：
{{
    "recommendations": [
        {{"career": "职业名称", "matchScore": 匹配度, "reason": "推荐理由"}},
        {{"career": "职业名称", "matchScore": 匹配度, "reason": "推荐理由"}},
        {{"career": "职业名称", "matchScore": 匹配度, "reason": "推荐理由"}}
    ],
    "analysis_result": "对用户的综合分析和职业建议"
}}
"""
        prompt = ChatPromptTemplate.from_messages([
            ('system', system_prompt),
            ('user', self_introduction)
        ])
        
        # 调用大模型
        chain = prompt | llm
        result = chain.invoke({})
        
        # 解析响应
        import json
        try:
            response_data = json.loads(result.content)
        except:
            # 如果不是有效的JSON，返回默认推荐
            response_data = {
                "recommendations": [
                    {"career": "后端开发工程师", "matchScore": 85, "reason": "基于您的技能背景推荐"},
                    {"career": "全栈工程师", "matchScore": 80, "reason": "综合您的技术能力推荐"},
                    {"career": "软件工程师", "matchScore": 75, "reason": "根据您的职业期望推荐"}
                ],
                "analysis_result": result.content
            }
        
        llm_time = time.time() - start_time
        logger.info(f"Simple LLM recommendation completed in {llm_time:.2f}s")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Simple LLM recommendation error: {str(e)}")
        # 返回默认推荐
        return {
            "recommendations": [
                {"career": "后端开发工程师", "matchScore": 85, "reason": "基于通用技能推荐"},
                {"career": "前端开发工程师", "matchScore": 80, "reason": "综合能力匹配"},
                {"career": "全栈工程师", "matchScore": 75, "reason": "广泛职业发展方向"}
            ],
            "analysis_result": f"LLM调用异常: {str(e)}"
        }


def _generate_llm_recommendation(self_introduction: str, user=None) -> dict:
    """
    异步生成LLM推荐结果
    
    Args:
        self_introduction: 用户自我介绍
        user: 用户对象
        
    Returns:
        包含推荐结果的字典
    """
    try:
        logger.info("Starting LLM recommendation generation")
        
        # 获取职业分类信息
        from ai_integration.langgraph.utils.prompt_manager import get_career_categories, get_prompt
        logger.info("Getting career categories")
        career_info = get_career_categories()
        logger.info(f"Career info length: {len(career_info)}")
        
        logger.info("Getting recommendation prompt")
        recommendation_prompt = get_prompt('recommendation')
        logger.info(f"Recommendation prompt length: {len(recommendation_prompt)}")
        
        # 限制提示词长度，避免提示词过长导致处理时间增加
        max_self_intro_length = 500
        max_career_info_length = 1000
        
        if len(self_introduction) > max_self_intro_length:
            self_introduction = self_introduction[:max_self_intro_length] + "..."
        
        if len(career_info) > max_career_info_length:
            career_info = career_info[:max_career_info_length] + "..."
        
        # 构建完整的提示词
        enhanced_prompt = "用户自我介绍：" + self_introduction + "\n\n" + career_info + "\n\n" + recommendation_prompt
        logger.info(f"Enhanced prompt length: {len(enhanced_prompt)}")
        
        # 创建工作流并执行
        logger.info("Creating chat workflow")
        chat_workflow = create_chat_workflow()
        
        # 检查环境变量
        api_key = settings.LLM_API_KEY
        base_url = settings.LLM_BASE_URL
        logger.warning(f"API Key: {'Set' if api_key else 'Not set'}")
        logger.warning(f"Base URL: {base_url}")
        
        # 使用新的AgentState格式
        from langchain_core.messages import HumanMessage
        state = {
            "messages": [HumanMessage(content=enhanced_prompt)],
            "mode": "recommendation",
            "response": ""
        }
        
        logger.info("Invoking LangGraph workflow for career recommendation")
        try:
            result = chat_workflow.invoke(state)
            logger.info(f"LangGraph result type: {type(result)}")
            logger.info(f"LangGraph result: {result}")
        except Exception as e:
            logger.error(f"LangGraph invocation error: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
        # 提取响应内容
        response_content = result.get("response", "")
        logger.info(f"LLM response length: {len(response_content)}")
        
        # 解析推荐结果
        processed_recommendations = []
        cards = []
        accordion = None
        
        try:
            # 尝试从JSON块中提取
            import re
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_content)
            if json_match:
                logger.info(f"✅ Found JSON block in response")
                clean_content = json_match.group(1).strip()
                logger.info(f"Clean content length: {len(clean_content)}")
                clean_content = clean_content.replace('{{', '{').replace('}}', '}')
                try:
                    parsed_content = json.loads(clean_content, strict=False)
                    logger.info(f"✅ JSON parsed successfully")
                    
                    # 新格式：包含 cards 和 accordion
                    if isinstance(parsed_content, dict):
                        if 'cards' in parsed_content and isinstance(parsed_content['cards'], list):
                            cards = parsed_content['cards']
                            processed_recommendations = cards  # 兼容旧格式
                            logger.info(f"✅ Found cards: {len(cards)} items")
                        if 'accordion' in parsed_content and isinstance(parsed_content['accordion'], dict):
                            accordion = parsed_content['accordion']
                            logger.info(f"✅ Found accordion with {len(accordion.get('careers', []))} careers")
                        # 旧格式：包含 recommendations
                        elif 'recommendations' in parsed_content:
                            processed_recommendations = parsed_content['recommendations']
                            logger.info(f"⚠️ Using old format: recommendations")
                    elif isinstance(parsed_content, list):
                        processed_recommendations = parsed_content
                        logger.info(f"⚠️ JSON is a list directly")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error: {str(e)}")
                    logger.error(f"Problematic content snippet: {clean_content[:200]}")
            else:
                logger.info(f"❌ No JSON block found in response")
        except Exception as e:
            logger.error(f"❌ Error parsing JSON: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        # 如果JSON解析失败，尝试从文本中提取
        if not processed_recommendations:
            career_matches = re.findall(r'###\s*(.*?)\s*', response_content)
            for i, career in enumerate(career_matches[:3]):
                career_name = career.strip()
                if career_name:
                    processed_recommendations.append({
                        "career": career_name,
                        "matchScore": 90 - i*10,
                        "reason": "基于您的背景和技能推荐",
                        "skillsMatch": [],
                        "missingSkills": [],
                        "improvement": ""
                    })
        
        # 确保至少返回三个推荐
        if len(processed_recommendations) < 3:
            fallback = [
                {"career": "后端工程师", "matchScore": 90, "reason": "基于您的技能推荐"},
                {"career": "前端工程师", "matchScore": 80, "reason": "基于您的兴趣推荐"},
                {"career": "全栈工程师", "matchScore": 70, "reason": "综合推荐"}
            ]
            processed_recommendations.extend(fallback[len(processed_recommendations):])
        
        logger.info(f"Generated {len(processed_recommendations)} recommendations")
        
        result = {
            "recommendations": processed_recommendations[:3],
            "analysis_result": response_content,
            "source": "llm"
        }
        
        # 添加新格式的数据（如果存在）
        if cards:
            result["cards"] = cards[:3]
        if accordion:
            result["accordion"] = accordion
        
        return result
        
    except Exception as e:
        logger.error(f"Error in LLM generation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise  # 抛出异常，让调用者处理


def _save_recommendation_record_simple(self_introduction: str, recommendations: list, 
                                       analysis_result: str, user=None) -> str:
    """
    简化版保存推荐记录 - 只保存到数据库，跳过LanceDB
    
    Args:
        self_introduction: 用户自我介绍
        recommendations: 推荐结果
        analysis_result: 分析结果
        user: 用户对象
        
    Returns:
        会话ID
    """
    try:
        # 生成会话ID
        session_id = os.urandom(16).hex()
        
        # 保存到数据库
        record, created = CareerRecommendationRecord.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': user,
                'self_introduction': self_introduction,
                'recommendations': recommendations,
                'analysis_result': analysis_result
            }
        )
        
        if not created:
            record.user = user
            record.self_introduction = self_introduction
            record.recommendations = recommendations
            record.analysis_result = analysis_result
            record.save()
        
        # 保存使用记录
        try:
            AIUsageRecord.objects.create(
                user=user,
                usage_type='recommendation',
                related_id=session_id
            )
        except Exception as e:
            logger.error(f"Error creating AIUsageRecord: {str(e)}")
        
        logger.info(f"Saved recommendation record: {session_id}")
        return session_id
        
    except Exception as e:
        logger.error(f"Error saving recommendation record: {str(e)}")
        return ""


def _save_recommendation_record(self_introduction: str, recommendations: list, 
                                analysis_result: str, user=None) -> str:
    """
    异步保存推荐记录到数据库和LanceDB
    
    Args:
        self_introduction: 用户自我介绍
        recommendations: 推荐结果
        analysis_result: 分析结果
        user: 用户对象
        
    Returns:
        会话ID
    """
    try:
        # 生成会话ID
        session_id = os.urandom(16).hex()
        
        # 保存到数据库
        record, created = CareerRecommendationRecord.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': user,
                'self_introduction': self_introduction,
                'recommendations': recommendations,
                'analysis_result': analysis_result
            }
        )
        
        if not created:
            record.user = user
            record.self_introduction = self_introduction
            record.recommendations = recommendations
            record.analysis_result = analysis_result
            record.save()
        
        # 保存到LanceDB
        career_search = get_career_search()
        career_search.add_record({
            "id": str(record.id),
            "user_id": str(user.id) if user else "",
            "self_introduction": self_introduction,
            "recommendations": json.dumps(recommendations),
            "analysis_result": analysis_result,
            "created_at": record.created_at.isoformat()
        })
        
        # 保存使用记录
        try:
            AIUsageRecord.objects.create(
                user=user,
                usage_type='recommendation',
                related_id=session_id
            )
        except Exception as e:
            logger.error(f"Error creating AIUsageRecord: {str(e)}")
        
        logger.info(f"Saved recommendation record: {session_id}")
        return session_id
        
    except Exception as e:
        logger.error(f"Error saving recommendation record: {str(e)}")
        return ""


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def optimized_career_recommendation(request):
    """
    优化后的职业推荐API接口 - 直接调用LLM生成推荐
    
    简化流程：跳过复杂的LangGraph工作流，直接调用大模型生成职业推荐
    """
    # 记录开始时间
    start_time = time.time()
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        self_introduction = data.get('self_introduction', '')
        
        if not self_introduction:
            return JsonResponse({'error': 'self_introduction is required'}, status=400)
        
        logger.info(f"Received career recommendation request: {self_introduction[:100]}...")
        
        # 阶段1: 检查缓存
        cache_start = time.time()
        cached_result = _get_cached_result(self_introduction)
        cache_time = time.time() - cache_start
        
        # 如果有缓存，直接返回
        if cached_result:
            logger.info("Using cached result")
            total_time = time.time() - start_time
            return JsonResponse({
                "success": True,
                "recommendations": cached_result.get("recommendations", []),
                "raw_analysis": cached_result.get("raw_analysis", ""),
                "session_id": cached_result.get("session_id", "cached"),
                "source": "cache",
                "match_score": cached_result.get("match_score", 0),
                "response_time": total_time,
                "timing": {
                    "cache_check": cache_time,
                    "total": total_time
                }
            })
        
        # 阶段2: A-RAG搜索（获取职业数据作为参考）
        search_start = time.time()
        logger.info("Starting A-RAG search")
        
        try:
            career_search = get_career_search()
            # 使用更宽松的阈值和更短的超时时间
            search_results = career_search.search_with_cache(
                self_introduction,
                keyword_threshold=0.5,
                semantic_threshold=0.6,
                top_k=3,
                timeout=10  # 设置10秒超时
            )
            logger.info(f"A-RAG search completed, found {len(search_results)} results")
        except Exception as e:
            logger.error(f"A-RAG search error: {str(e)}")
            search_results = []
        
        search_time = time.time() - search_start
        
        # 计算匹配程度
        match_score = 0
        if search_results:
            match_score = search_results[0].get("match_score", 0)
        
        # 阶段3: 使用LangGraph工作流生成LLM推荐
        user = request.user if request.user.is_authenticated else None
        
        try:
            # 使用完整的LangGraph工作流
            llm_result = _generate_llm_recommendation(self_introduction, user)
            
            # 保存到数据库和LanceDB
            session_id = _save_recommendation_record(
                self_introduction,
                llm_result["recommendations"],
                llm_result["analysis_result"],
                user
            )
            
            # 缓存结果
            _set_cached_result(self_introduction, llm_result)
            
            total_time = time.time() - start_time
            logger.info(f"LLM generation completed. Total time: {total_time:.2f}s")
            
            response_data = {
                "success": True,
                "recommendations": llm_result["recommendations"],
                "raw_analysis": llm_result["analysis_result"],
                "session_id": session_id,
                "source": "llm",
                "match_score": match_score,
                "response_time": total_time,
                "timing": {
                    "cache_check": cache_time,
                    "arag_search": search_time,
                    "llm_generation": total_time - cache_time - search_time,
                    "total": total_time
                }
            }
            
            # 添加新格式的数据（如果存在）
            if "cards" in llm_result and llm_result["cards"]:
                response_data["cards"] = llm_result["cards"]
                logger.info(f"✅ Added cards to response: {len(llm_result['cards'])} items")
            if "accordion" in llm_result and llm_result["accordion"]:
                response_data["accordion"] = llm_result["accordion"]
                logger.info(f"✅ Added accordion to response")
            
            return JsonResponse(response_data)
        except Exception as e:
            logger.error(f"Error in LLM generation: {str(e)}")
            # 如果LLM生成失败，使用简化版LLM作为备选
            try:
                llm_result = _simple_llm_recommendation(self_introduction)
                session_id = _save_recommendation_record_simple(
                    self_introduction,
                    llm_result["recommendations"],
                    llm_result["analysis_result"],
                    user
                )
                _set_cached_result(self_introduction, llm_result)
                
                total_time = time.time() - start_time
                response_data = {
                    "success": True,
                    "recommendations": llm_result["recommendations"],
                    "raw_analysis": llm_result["analysis_result"],
                    "session_id": session_id,
                    "source": "llm_fallback",
                    "match_score": match_score,
                    "response_time": total_time,
                    "timing": {
                        "cache_check": cache_time,
                        "arag_search": search_time,
                        "llm_generation": total_time - cache_time - search_time,
                        "total": total_time
                    }
                }
                return JsonResponse(response_data)
            except Exception as fallback_e:
                logger.error(f"Fallback LLM also failed: {str(fallback_e)}")
                # 如果都失败，使用默认推荐
                default_recommendations = [
                {"career": "后端工程师", "matchScore": 85, "reason": "基于您的技能推荐"},
                {"career": "前端工程师", "matchScore": 80, "reason": "基于您的兴趣推荐"},
                {"career": "全栈工程师", "matchScore": 75, "reason": "综合推荐"}
            ]
            total_time = time.time() - start_time
            return JsonResponse({
                "success": True,
                "recommendations": default_recommendations,
                "raw_analysis": "AI生成失败，使用默认推荐",
                "session_id": "default",
                "source": "default",
                "match_score": match_score,
                "response_time": total_time,
                "timing": {
                    "cache_check": cache_time,
                    "arag_search": search_time,
                    "total": total_time
                }
            })
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Error in optimized_career_recommendation after {total_time:.2f}s: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e),
            "response_time": total_time
        }, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def read_career_chunk(request, record_id):
    """
    Chunk Read API - 根据ID读取完整的职业推荐记录
    
    Args:
        record_id: 记录ID
        
    Returns:
        完整的推荐记录
    """
    try:
        start_time = time.time()
        
        career_search = get_career_search()
        result = career_search.read_chunk(record_id)
        
        total_time = time.time() - start_time
        
        if result.get("success"):
            return JsonResponse({
                "success": True,
                "record": result.get("record"),
                "read_time": result.get("read_time", 0),
                "source": result.get("source", "lancedb"),
                "total_time": total_time
            })
        else:
            return JsonResponse({
                "success": False,
                "error": result.get("error", "Unknown error"),
                "total_time": total_time
            }, status=404)
            
    except Exception as e:
        logger.error(f"Error in read_career_chunk: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def read_career_chunks_batch(request):
    """
    批量Chunk Read API - 根据多个ID读取完整的职业推荐记录
    
    请求体:
    {
        "record_ids": ["id1", "id2", "id3"]
    }
    
    Returns:
        包含所有记录的字典
    """
    try:
        start_time = time.time()
        
        data = json.loads(request.body)
        record_ids = data.get('record_ids', [])
        
        if not record_ids:
            return JsonResponse({
                "success": False,
                "error": "record_ids is required"
            }, status=400)
        
        career_search = get_career_search()
        result = career_search.read_chunks(record_ids)
        
        total_time = time.time() - start_time
        
        if result.get("success"):
            return JsonResponse({
                "success": True,
                "records": result.get("records", []),
                "errors": result.get("errors", []),
                "read_time": result.get("read_time", 0),
                "total_time": total_time
            })
        else:
            return JsonResponse({
                "success": False,
                "error": result.get("error", "Unknown error"),
                "total_time": total_time
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error in read_career_chunks_batch: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def arag_career_recommendation(request):
    """
    A-RAG职业推荐API - 使用A-RAG代理进行职业推荐
    
    请求体:
    {
        "self_introduction": "用户自我介绍内容"
    }
    
    Returns:
        职业推荐结果
    """
    try:
        start_time = time.time()
        
        data = json.loads(request.body)
        self_introduction = data.get('self_introduction', '')
        
        if not self_introduction:
            return JsonResponse({
                "success": False,
                "error": "self_introduction is required"
            }, status=400)
        
        # 获取ARAG代理实例
        arag_agent = get_arag_agent()
        
        # 调用ARAG代理进行推荐
        recommendation = arag_agent.agent_recommend(self_introduction)
        
        # 生成会话ID
        session_id = 'arag_' + str(int(time.time())) + '_' + str(hash(self_introduction) % 10000)
        
        # 构建分析结果
        analysis_result = ""
        if recommendation.get('recommendations'):
            analysis_result = "# 大模型职业推荐分析\n\n"
            for i, rec in enumerate(recommendation['recommendations'], 1):
                analysis_result += f"## {i}. {rec['career']} (匹配度: {rec['matchScore']}%)\n"
                analysis_result += f"### 推荐理由\n{rec['reason']}\n"
                if rec.get('skillsMatch'):
                    analysis_result += f"### 技能匹配\n{', '.join(rec['skillsMatch'])}\n"
                if rec.get('missingSkills'):
                    analysis_result += f"### 缺失技能\n{', '.join(rec['missingSkills'])}\n"
                if rec.get('improvement'):
                    analysis_result += f"### 提升建议\n{rec['improvement']}\n\n"
        
        # 保存推荐记录到数据库（异步执行）
        def save_recommendation_record():
            try:
                user = request.user if request.user.is_authenticated else None
                
                # 保存到数据库
                record, created = CareerRecommendationRecord.objects.get_or_create(
                    session_id=session_id,
                    defaults={
                        'user': user,
                        'self_introduction': self_introduction,
                        'recommendations': recommendation.get('recommendations', []),
                        'analysis_result': analysis_result
                    }
                )
                
                if not created:
                    record.user = user
                    record.self_introduction = self_introduction
                    record.recommendations = recommendation.get('recommendations', [])
                    record.analysis_result = analysis_result
                    record.save()
                
                # 同步到LanceDB
                career_search = get_career_search()
                career_search.add_record({
                    "id": str(record.id),
                    "user_id": str(user.id) if user else "",
                    "self_introduction": self_introduction,
                    "recommendations": json.dumps(recommendation.get('recommendations', [])),
                    "analysis_result": analysis_result,
                    "created_at": record.created_at.isoformat()
                })
                
                # 保存使用记录
                try:
                    AIUsageRecord.objects.create(
                        user=user,
                        usage_type='recommendation',
                        related_id=session_id
                    )
                except Exception as e:
                    logger.error(f"Error creating AIUsageRecord: {str(e)}")
                
                logger.info(f"Saved A-RAG recommendation record: {session_id}")
            except Exception as e:
                logger.error(f"Error saving A-RAG recommendation record: {str(e)}")
        
        # 在后台线程中执行保存操作
        _thread_pool.submit(save_recommendation_record)
        
        total_time = time.time() - start_time
        
        return JsonResponse({
            "success": True,
            "recommendation": recommendation,
            "session_id": session_id,
            "response_time": total_time,
            "raw_analysis": analysis_result
        })
        
    except Exception as e:
        logger.error(f"Error in arag_career_recommendation: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def health_check(request):
    """
    健康检查端点
    
    Returns:
        健康状态
    """
    try:
        logger.info("Health check request received")
        return JsonResponse({
            "success": True,
            "status": "healthy",
            "message": "AI integration service is running"
        })
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JsonResponse({
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }, status=500)


@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def approve_senior_advice(request, advice_id):
    """
    审核学长学姐建议API
    
    只能由管理员调用
    """
    try:
        # 检查用户是否为管理员
        if not request.user.is_staff:
            return JsonResponse({
                "success": False,
                "error": "Permission denied"
            }, status=403)
        
        # 获取建议
        advice = SeniorAdvice.objects.get(id=advice_id)
        advice.is_approved = True
        advice.save()
        
        return JsonResponse({
            "success": True,
            "message": "审核通过"
        })
    except SeniorAdvice.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Advice not found"
        }, status=404)
    except Exception as e:
        logger.error(f"Error approving senior advice: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def voice_to_resume(request):
    """
    语音生成简历API
    
    接收语音识别文本，通过大模型分析生成简历内容
    """
    try:
        # 获取语音识别文本
        voice_text = request.data.get('voice_text', '')
        if not voice_text:
            return JsonResponse({
                "success": False,
                "message": "语音文本不能为空"
            }, status=400)
        
        # 从数据库获取提示词
        from ai_integration.langgraph.utils.prompt_manager import get_prompt
        system_prompt = get_prompt('resume')
        
        # 构建用户提示词
        prompt = f"""
        用户语音文本：
        {voice_text}
        """
        
        # 组合提示词
        prompt = system_prompt + "\n" + prompt
        
        # 调用大模型
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import JsonOutputParser
        
        # 配置大模型
        llm = ChatOpenAI(
            **get_llm_kwargs(),
        )
        
        # 创建提示模板
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个专业的简历生成助手，根据用户提供的语音输入生成结构化的简历数据。"),
            ("user", prompt)
        ])
        
        # 创建输出解析器
        parser = JsonOutputParser()
        
        # 构建链
        chain = chat_prompt | llm | parser
        
        # 执行链
        result = chain.invoke({})
        
        # 处理生成的结果
        generated_resume = {
            "name": result.get('name', ''),
            "target_position": result.get('target_position', ''),
            "phone": result.get('phone', ''),
            "email": result.get('email', ''),
            "address": result.get('address', ''),
            "self_evaluation": result.get('self_evaluation', ''),
            "skills": result.get('skills', ''),
            "education": result.get('education', []),
            "experience": result.get('experience', []),
            "projects": result.get('projects', []),
            "certificates": result.get('certificates', []),
            "awards": result.get('awards', [])
        }
        
        return JsonResponse({
            "success": True,
            "data": generated_resume,
            "message": "简历生成成功"
        })
    except Exception as e:
        logger.error(f"Error generating resume from voice: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e),
            "message": "简历生成失败"
        }, status=500)
