import os
import json
import time
import re as regex
import threading
import hashlib
import asyncio
import base64
import uuid
from queue import Queue
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from cs_career_guide.ai_config import get_llm_kwargs
from ai_integration.interview.legacy import extract_section, extract_score  # Compatibility exports.
from cs_career_guide.vector_store import CAREER_TABLE_NAME, open_career_table
from ai_integration.models import AIConversation, AITag, CareerEvaluationRecord, CareerPlanReport, AIUsageRecord, CareerRecommendationRecord, AIChatPair, InterviewReviewRecord
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
import logging

try:
    import lancedb
    import pyarrow as pa
    VECTOR_IMPORT_ERROR = None
except ImportError as exc:
    lancedb = None
    pa = None
    VECTOR_IMPORT_ERROR = exc
    logging.getLogger(__name__).warning(
        'LanceDB/PyArrow unavailable; semantic vector storage is disabled: %s', exc
    )

import websockets

# LangGraph integration
from ai_integration.langgraph.graphs.graph import create_chat_workflow
from ai_integration.langgraph.tools.time_tool import get_time
from ai_integration.langgraph.agents.memory_agent import memory_agent
from ai_integration.langgraph.utils.prompt_manager import get_prompt

# A-RAG integration
from ai_integration.arag_integration import get_career_search, ARAGCareerSearch

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

# LanceDB integration
def init_lancedb():
    """初始化LanceDB数据库"""
    if lancedb is None:
        raise RuntimeError('LanceDB is not installed in this runtime')
    # 创建LanceDB数据库目录
    db_path = str(settings.LANCEDB_PATH)
    os.makedirs(db_path, exist_ok=True)
    
    # 连接到LanceDB
    db = lancedb.connect(db_path)
    
    open_career_table(db, settings.EMBEDDING_DIMENSION)
    
    return db

def add_to_lancedb(record):
    """将职业推荐记录添加到LanceDB中"""
    try:
        # 准备数据
        data = {
            "id": str(record.id),
            "user_id": str(record.user.id) if record.user else "",
            "self_introduction": record.self_introduction,
            "introduction_preview": record.introduction_preview or "",
            "recommendations": json.dumps(record.recommendations, ensure_ascii=False),
            "analysis_result": record.analysis_result or "",
            "created_at": record.created_at.isoformat()
        }
        
        # 添加数据到LanceDB
        get_career_search().add_record(data)
        logger.info(f"Successfully added career recommendation record {record.id} to LanceDB")
    except Exception as e:
        logger.error(f"Error adding career recommendation record to LanceDB: {str(e)}")

def search_lancedb(self_introduction, threshold=0.7):
    """从LanceDB中检索匹配的职业推荐记录"""
    try:
        # 初始化LanceDB
        db = init_lancedb()
        table = db["career_recommendations"]
        
        # 获取所有记录
        results = table.to_pandas().to_dict('records')
        
        logger.info(f"Found {len(results)} records in LanceDB")
        
        # 过滤结果，只返回匹配度高的记录
        # 使用简单的关键词匹配算法
        filtered_results = []
        for result in results:
            # 计算关键词匹配度
            query_words = set(self_introduction.lower().split())
            record_words = set(result["self_introduction"].lower().split())
            
            # 避免除以零
            if not query_words:
                continue
                
            common_words = query_words.intersection(record_words)
            match_score = len(common_words) / len(query_words)
            
            logger.info(f"Record ID: {result['id']}, Match score: {match_score}")
            
            if match_score >= threshold:
                result["match_score"] = match_score
                filtered_results.append(result)
        
        logger.info(f"Filtered to {len(filtered_results)} matches with score >= {threshold}")
        
        # 按匹配度排序
        filtered_results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        return filtered_results
    except Exception as e:
        logger.error(f"Error searching LanceDB: {str(e)}")
        return []

logger = logging.getLogger(__name__)

User = get_user_model()

# LangGraph workflow will be created per request

# 已移除公司信息搜索相关函数（extract_search_params, search_company_info, build_prompt_with_company_info）

def build_user_profile_prompt(request):
    """从数据库获取用户数据并构建提示词"""
    user = None
    
    # 尝试从请求中获取用户
    if hasattr(request, 'user') and request.user.is_authenticated:
        user = request.user
    else:
        # 如果没有认证用户，尝试从请求头获取token并查找用户
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Token '):
            token = auth_header.split(' ')[1]
            from rest_framework.authtoken.models import Token
            try:
                token_obj = Token.objects.get(key=token)
                user = token_obj.user
            except Token.DoesNotExist:
                pass
    
    if not user:
        return ""
    
    # 构建用户信息提示词
    profile_parts = []
    
    # 基本信息
    if getattr(user, 'name', ''):
        profile_parts.append(f"姓名：{user.name}")
    if getattr(user, 'username', '') and not getattr(user, 'name', ''):
        profile_parts.append(f"用户名：{user.username}")
    if getattr(user, 'gender', ''):
        profile_parts.append(f"性别：{user.gender}")
    
    # 教育背景
    if getattr(user, 'school', ''):
        profile_parts.append(f"学校：{user.school}")
    if getattr(user, 'major', ''):
        profile_parts.append(f"专业：{user.major}")
    if getattr(user, 'grade', ''):
        profile_parts.append(f"年级：{user.grade}")
    if getattr(user, 'education', ''):
        profile_parts.append(f"学历：{user.education}")
    
    # 技能信息
    skills = []
    if getattr(user, 'skills', ''):
        skills.extend([s.strip() for s in str(user.skills).split(",") if s.strip()])
    if getattr(user, 'other_skills', ''):
        skills.extend([s.strip() for s in str(user.other_skills).split(",") if s.strip()])
    if skills:
        profile_parts.append(f"技能：{', '.join(skills)}")
    
    # 职业相关
    if getattr(user, 'career_goal', ''):
        profile_parts.append(f"职业期望：{user.career_goal}")
    if getattr(user, 'self_introduction', ''):
        profile_parts.append(f"自我介绍：{user.self_introduction}")
    if getattr(user, 'profile', ''):
        profile_parts.append(f"个人简介：{user.profile}")
    
    # 社交信息
    if getattr(user, 'github', ''):
        profile_parts.append(f"GitHub：{user.github}")
    
    if not profile_parts:
        return ""
    
    # 构建完整的提示词
    prompt = """【用户档案信息】
以下是用户的个人信息，请在回答时参考这些信息提供个性化的职业规划建议：

"""
    prompt += "\n".join(profile_parts)
    prompt += "\n\n"
    
    return prompt

@csrf_exempt
def llm_chat(request):
    # 记录开始时间
    start_time = time.time()
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # 解析请求数据
        requested_tts = False
        if request.FILES:
            user_message = request.POST.get('message', '')
            mode = request.POST.get('mode', '')
            interview_style = request.POST.get('interview_style', '')
            session_id = request.POST.get('session_id', '')
            if 'audio' in request.FILES:
                audio_file = request.FILES['audio']
                logger.info(f"Received audio file: {audio_file.name}, size: {audio_file.size}")
        else:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            mode = data.get('mode', '')
            interview_style = data.get('interview_style', '')
            session_id = data.get('session_id', '')
            requested_tts = data.get('enable_tts') is True
        
        logger.info(f"Received message: {user_message}, mode: {mode}, session_id: {session_id}")
        
        # 检查用户消息是否为空
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # 确定对话模式
        if mode == 'interview' or '【面试模式】' in user_message:
            actual_mode = 'interview'
        elif mode == 'interview_review' or '【面试复盘模式】' in user_message:
            actual_mode = 'review'
        elif mode == 'career_consultant' or mode == 'career' or '【职业规划师模式】' in user_message:
            actual_mode = 'career'
        else:
            actual_mode = 'normal'
        
        # 处理会话ID
        if not session_id:
            session_id = os.urandom(16).hex()
        
        # 获取或创建会话
        conversation, created = AIConversation.objects.get_or_create(
            session_id=session_id,
            defaults={
                'mode': actual_mode,
                'context_aware': True,
                'short_term_memory_size': 10
            }
        )
        
        # 获取短期记忆（最近的对话）
        chat_history = []
        if conversation.context_aware:
            # 获取最近的对话对
            recent_pairs = AIChatPair.objects.filter(conversation=conversation).order_by('-input_time')[:conversation.short_term_memory_size]
            # 构建聊天历史格式（保留完整对话）
            chat_history = []
            for pair in reversed(recent_pairs):
                chat_history.append({
                    'user': pair.user_input,
                    'ai': pair.ai_output  # 正确字段名是 ai_output
                })
        
        logger.info(f"Chat history length: {len(chat_history)}")
        
        # 其他模式的处理
        is_interview_mode = actual_mode == 'interview'
        is_review_mode = actual_mode == 'review'
        is_career_mode = actual_mode == 'career'
        is_normal_mode = actual_mode == 'normal'

        # Interview-specific behavior is selected through the application port.
        # HTTP/SSE, conversation storage and TTS remain shared infrastructure.
        interview_prompt = None
        if is_interview_mode or is_review_mode:
            from ai_integration.interview import get_interview_service
            interview_prompt = get_interview_service().prepare_turn(
                user_message, chat_history, interview_style, review=is_review_mode,
            )
            enhanced_prompt = interview_prompt.user
        else:
            context_prompt = ""
            if is_career_mode:
                user_profile_prompt = build_user_profile_prompt(request)
                if user_profile_prompt:
                    context_prompt = user_profile_prompt
            if chat_history:
                context_prompt += "对话历史：\n"
                for msg in chat_history:
                    if msg['user']:
                        context_prompt += f"用户：{msg['user']}\n"
                    if msg['ai']:
                        context_prompt += f"面试官：{msg['ai']}\n"
            enhanced_prompt = context_prompt + user_message
        mode_name = 'Career' if is_career_mode else ('Review' if is_review_mode else 'Interview' if is_interview_mode else 'Normal')
        logger.info(f"{mode_name} mode: using context-aware prompt")
        
        logger.info(f"Enhanced prompt length: {len(enhanced_prompt)}")
        
        # 使用LangGraph工作流处理请求
        try:
            logger.info("Using LangGraph workflow to process request")
            
            # 限制提示词长度
            max_prompt_length = 3000
            if interview_prompt is None and len(enhanced_prompt) > max_prompt_length:
                enhanced_prompt = enhanced_prompt[:max_prompt_length] + "..."
            
            def llm_chat_tts_work(llm, messages, mq, is_interview_mode_flag):
                async def run_tts_tasks():
                    enable_tts = settings.ENABLE_TTS and requested_tts
                    
                    if not is_interview_mode_flag or not enable_tts:
                        logger.info(f"TTS disabled - interview_mode={is_interview_mode_flag}, enable_tts={enable_tts}")
                        for chunk in llm.stream(messages):
                            if hasattr(chunk, "content") and chunk.content:
                                mq.put_nowait({'content': chunk.content})
                        return
                    
                    logger.warning("WARNING: TTS IS ENABLED - This will incur costs!")
                    
                    tts_api_key = settings.TTS_API_KEY
                    wss_url = settings.TTS_WSS_URL
             
                    headers = {"Authorization": f"Bearer {tts_api_key}"}
                    
                    try:
                    
                        if not all((tts_api_key, wss_url, settings.TTS_MODEL, settings.TTS_VOICE)):
                            raise ImproperlyConfigured("Configure TTS_API_KEY, TTS_WSS_URL, TTS_MODEL and TTS_VOICE")
                        llm_stream = llm.stream(messages)

                        
                    
                        async with websockets.connect(wss_url, additional_headers=headers) as ws:
                            task_id = uuid.uuid4().hex
                            run_task_msg = {
                                "header": {
                                    "action": "run-task",
                                    "task_id": task_id,
                                    "streaming": "duplex"
                                },
                                "payload": {
                                    "task_group": "audio",
                                    "task": "tts",
                                    "function": "SpeechSynthesizer",
                                    "model": settings.TTS_MODEL,
                                    "parameters": {
                                        "text_type": "PlainText",
                                        "voice": settings.TTS_VOICE,
                                        "format": "mp3",
                                        "sample_rate": 22050,
                                        "volume": 50,
                                        "rate": 1.25,
                                        "pitch": 1  
                                    },
                                    "input": { # input不能省去，不然会报错
                                    }
                                }
                            }
                            await ws.send(json.dumps(run_task_msg))
                            
                            # 等待大模型服务器发送 task-started
                            async for msg in ws:
                                data = json.loads(msg)
                                mq.put_nowait({'debug': f"Received message event: {data.get('header', {}).get('event', 'unknown')}"})
                                if data['header']['event'] == 'task-started':
                                    mq.put_nowait({'debug': "Task started, beginning TTS stream"})
                                    break
                                    
                            
                            async def tts_sender():
                                for chunk in llm_stream:
                                    if hasattr(chunk, "content") and chunk.content:
                                        content = chunk.content
                                        
                                        mq.put_nowait({'content': content})
                                        await ws.send(json.dumps({
                                            "header": {
                                                "action": "continue-task",
                                                "task_id": task_id,
                                                "streaming": "duplex"
                                            },
                                            "payload": {"input": {"text": content}}
                                        }))
                                
                                await ws.send(json.dumps({
                                    "header": {
                                        "action": "finish-task",
                                        "task_id": task_id
                                    },
                                    "payload": {"input": {}}
                                }))
                            
                            async def tts_receiver():
                            
                                async for msg in ws:
                                    if isinstance(msg, bytes):
                                        audio = base64.b64encode(msg).decode('utf8')
                                      
                                        mq.put_nowait({'audio': audio})
                                    else:
                                        
                                        data = json.loads(msg)
                                        event = data['header'].get('event', 'unknown')
                                            
                                        if event in ['task-finished', 'task-failed']:
                                            break
                                        
                            await asyncio.gather(tts_sender(), tts_receiver())
                            
                    except Exception as e:
                        mq.put_nowait({'debug': f"TTS error: {str(e)}"})
                        logger.error(f"TTS error, falling back to text only: {str(e)}")
                        for chunk in llm.stream(messages):
                            if hasattr(chunk, "content") and chunk.content:
                                mq.put_nowait({'content': chunk.content})
                # work 协程
                try:
                    asyncio.run(run_tts_tasks())
                
                finally:
                    
                    mq.put_nowait(None)
            
            def stream_generator():
                response_content = ""
                
                from langchain_openai import ChatOpenAI
                
                llm = ChatOpenAI(
                    temperature=0.7,
                    **get_llm_kwargs(),
                )
                
                from ai_integration.langgraph.utils.prompt_manager import get_prompt
                
                if interview_prompt is not None:
                    system_prompt = interview_prompt.system
                elif is_career_mode:
                    system_prompt = get_prompt('career')
                else:
                    system_prompt = get_prompt('chat')
                
                from langchain_core.messages import SystemMessage, HumanMessage
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=enhanced_prompt)
                ]

                # event_stream 主线程-同步生成器
                mq = Queue()
                thread = threading.Thread(target=llm_chat_tts_work, args=(llm, messages, mq, is_interview_mode))
                thread.start()
                
                try:
                    while True:
                        msg = mq.get()
                        if msg is None:
                            break
                        if msg.get('content', None):
                            response_content += msg['content']
                            chunk_data = {"type": "chunk", "content": msg['content']}
                            yield f'data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n'
                        if msg.get('audio', None):
                            audio_data = {"type": "audio", "audio": msg['audio']}
                            yield f'data: {json.dumps(audio_data, ensure_ascii=False)}\n\n'
                    
                    yield "data: [DONE]\n\n"  # 这是一种约定俗成的结束标记
                except Exception as e:
                    logger.error(f"Error during streaming: {str(e)}")
                    error_data = {"type": "error", "content": f"生成响应时出错: {str(e)}"}
                    yield f'data: {json.dumps(error_data, ensure_ascii=False)}\n\n'
                
                if response_content:
                    now = datetime.now()
                    chat_pair = AIChatPair.objects.create(
                        conversation=conversation,
                        user_input=user_message,
                        ai_output=response_content,
                        input_time=now,
                        output_time=now
                    )
                    
                    def process_memory():
                        try:
                            memory_agent.process_conversation(session_id)
                        except Exception as e:
                            logger.error(f"Error processing memory in background: {str(e)}")
                    
                    memory_thread = threading.Thread(target=process_memory)
                    memory_thread.daemon = True
                    memory_thread.start()
                    
                    if conversation.context_aware:
                        all_pairs = AIChatPair.objects.filter(conversation=conversation).order_by('-input_time')
                        if all_pairs.count() > conversation.short_term_memory_size:
                            oldest_pairs = all_pairs[conversation.short_term_memory_size:]
                            for pair in oldest_pairs:
                                pair.delete()
                
                yield f'data: {{"type": "end", "session_id": "{session_id}"}}\n\n'
            
            response = StreamingHttpResponse(stream_generator(), content_type='text/event-stream; charset=utf-8')
            response['Content-Encoding'] = 'utf-8'
            return response
        except Exception as e:
            logger.error(f"LangGraph execution error: {str(e)}")
            
            # 直接返回错误，不使用模拟响应
            total_time = time.time() - start_time
            return JsonResponse({
                "success": False,
                "error": f"LLM生成失败: {str(e)}",
                "response_time": total_time
            }, status=500)
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Error in llm_chat after {total_time:.2f}s: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e),
            "response_time": total_time
        }, status=500)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def save_chat_record(request):
    """保存聊天记录的API接口"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        session_id = data.get('session_id', '')
        user_message = data.get('user_message', '')
        assistant_message = data.get('assistant_message', '')
        mode = data.get('mode', 'normal')
        
        if not session_id:
            return JsonResponse({'error': 'session_id is required'}, status=400)
        
        user = None
        logger.info(f"Request user: {request.user}")
        logger.info(f"Request auth: {request.auth}")
        logger.info(f"Is authenticated: {request.user.is_authenticated}")
        if request.user.is_authenticated:
            user = request.user
        
        conversation, created = AIConversation.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': user,
                'mode': mode
            }
        )
        
        if not created:
            conversation.user = user
            conversation.mode = mode
            conversation.save()
        
        # 使用新的AIChatPair模型存储聊天记录
        import datetime
        now = datetime.datetime.now()
        chat_pair = AIChatPair.objects.create(
            conversation=conversation,
            user_input=user_message,
            ai_output=assistant_message,
            input_time=now,
            output_time=now
        )
        
        # 根据聊天模式设置不同的使用类型
        usage_type = 'chat'
        if mode == 'career':
            usage_type = 'career_consultant'
        elif mode == 'normal':
            usage_type = 'chat'
        
        # 保存统一使用记录
        try:
            AIUsageRecord.objects.create(
                user=user,
                usage_type=usage_type,
                related_id=session_id
            )
        except Exception as e:
            logger.error(f"Error creating AIUsageRecord: {str(e)}")
        
        logger.info(f"Chat record saved: session_id={session_id}, mode={mode}, user={user.username if user else 'anonymous'}")
        
        return JsonResponse({'success': True, 'conversation_id': conversation.id, 'pair_id': chat_pair.id})
    
    except Exception as e:
        logger.error(f"Error in save_chat_record: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def save_career_evaluation(request):
    """保存职业评测记录的API接口"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        session_id = data.get('session_id', '')
        selected_careers = data.get('selected_careers', [])
        evaluation_result = data.get('evaluation_result', {})
        
        if not session_id:
            return JsonResponse({'error': 'session_id is required'}, status=400)
        
        user = None
        logger.info(f"Request user: {request.user}")
        logger.info(f"Request auth: {request.auth}")
        logger.info(f"Is authenticated: {request.user.is_authenticated}")
        if request.user.is_authenticated:
            user = request.user
        
        record, created = CareerEvaluationRecord.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': user,
                'selected_careers': selected_careers,
                'evaluation_result': evaluation_result
            }
        )
        
        if not created:
            record.user = user
            record.selected_careers = selected_careers
            record.evaluation_result = evaluation_result
            record.save()
        
        # 保存统一使用记录
        try:
            AIUsageRecord.objects.create(
                user=user,
                usage_type='evaluation',
                related_id=session_id
            )
        except Exception as e:
            logger.error(f"Error creating AIUsageRecord: {str(e)}")
        
        logger.info(f"Career evaluation saved: session_id={session_id}, user={user.username if user else 'anonymous'}")
        
        return JsonResponse({'success': True, 'record_id': record.id})
    
    except Exception as e:
        logger.error(f"Error in save_career_evaluation: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def career_recommendation(request):
    """职业推荐API接口 - 先从LanceDB检索匹配记录，再调用agent处理"""
    # 记录开始时间
    start_time = time.time()
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        self_introduction = data.get('self_introduction', '')
        
        if not self_introduction:
            return JsonResponse({'error': 'self_introduction is required'}, status=400)
        
        logger.info(f"Received career recommendation request with self_introduction length: {len(self_introduction)}")
        
        # 先从LanceDB中检索匹配的职业推荐记录（不是缓存，是数据检索）
        lancedb_start = time.time()
        logger.info("Searching for matching recommendations in LanceDB")
        lancedb_results = search_lancedb(self_introduction)
        lancedb_end = time.time()
        logger.info(f"LanceDB search took {lancedb_end - lancedb_start:.2f} seconds")
        
        # 创建工作流并执行（agent -> tool -> agent 流程）
        llm_start = time.time()
        chat_workflow = create_chat_workflow()
        
        # 正确构建状态 - 使用 messages（消息序列）而不是 message
        from langchain_core.messages import HumanMessage
        state = {
            "messages": [HumanMessage(content=self_introduction)],
            "mode": "recommendation",
            "response": "",
            "tool_calls": None,
            "tool_results": None,
            "last_agent": None,
            "lancedb_results": lancedb_results  # 将LanceDB结果传入状态，供agent参考
        }
        
        logger.info("Invoking LangGraph workflow for career recommendation")
        logger.info(f"Input state: mode={state['mode']}, messages count={len(state['messages'])}, lancedb_results={len(lancedb_results) if lancedb_results else 0}")
        result = chat_workflow.invoke(state)
        logger.info(f"LangGraph result keys: {list(result.keys())}")
        logger.info(f"LangGraph result: {result}")
        
        # 提取响应内容
        response_content = result.get("response", "")
        logger.info(f"Extracted response content: {response_content}")
        # 记录完整的响应内容，以便调试
        logger.info(f"Full response content length: {len(response_content)}")
        if len(response_content) > 1000:
            logger.info(f"First 1000 characters of response: {response_content[:1000]}...")
        else:
            logger.info(f"Full response: {response_content}")
        
        # 打印AI的原始输出，以便调试
        print("\n=== AI ORIGINAL OUTPUT ===")
        print(response_content)
        print("=== END AI ORIGINAL OUTPUT ===\n")
        llm_end = time.time()
        logger.info(f"LLM generation took {llm_end - llm_start:.2f} seconds")
        
        # 生成会话ID
        session_id = os.urandom(16).hex()
        
        # 保存推荐记录
        user = None
        if request.user.is_authenticated:
            user = request.user
        
        # 尝试解析推荐结果为JSON格式
        parse_start = time.time()
        processed_recommendations = []
        try:
            # 打印AI的原始输出，以便调试
            print("\n=== AI ORIGINAL OUTPUT ===")
            print(response_content)
            print("=== END AI ORIGINAL OUTPUT ===\n")
            
            # 尝试从响应内容中提取JSON格式的推荐结果
            # 使用正则表达式提取JSON块
            json_match = regex.search(r'```json\s*([\s\S]*?)\s*```', response_content)
            if json_match:
                clean_content = json_match.group(1).strip()
                logger.info(f"Found JSON block: {clean_content[:200]}...")
                
                # 修复可能由转义大括号引起的问题
                clean_content = clean_content.replace('{{', '{').replace('}}', '}')
                
                try:
                    parsed_content = json.loads(clean_content, strict=False)
                    logger.info(f"Parsed JSON content: {parsed_content}")
                    
                    if isinstance(parsed_content, dict) and 'recommendations' in parsed_content:
                        # 如果已经是包含recommendations字段的对象
                        processed_recommendations = parsed_content['recommendations']
                        logger.info(f"Parsed recommendations from JSON: {processed_recommendations}")
                    elif isinstance(parsed_content, list):
                        # 如果直接是数组
                        processed_recommendations = parsed_content
                        logger.info(f"Using array recommendations: {processed_recommendations}")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode failed: {str(e)}")
            
            # 如果没有从JSON中提取到推荐结果，尝试从文本中提取
            if not processed_recommendations:
                logger.info("No recommendations found in JSON, trying to extract from text")
                # 尝试从文本中提取职业推荐
                # 尝试匹配以###开头的职业名称
                career_matches = regex.findall(r'###\s*(.*?)\s*', response_content)
                logger.info(f"Found career matches: {career_matches}")
                
                # 构建推荐列表
                for i, career in enumerate(career_matches[:3]):
                    career_name = career.strip()
                    if career_name:
                        # 计算匹配度
                        match_score = 90 - i*10
                        processed_recommendations.append({
                            "career": career_name,
                            "matchScore": match_score,
                            "reason": "基于您的背景和技能推荐",
                            "skillsMatch": [],
                            "missingSkills": [],
                            "improvement": ""
                        })
                
                logger.info(f"Extracted {len(processed_recommendations)} recommendations from text")
        except Exception as e:
            logger.error(f"Error parsing recommendations: {str(e)}")
            # 如果解析失败，尝试从文本中提取
            try:
                logger.info("Trying to extract recommendations from text after error")
                # 尝试从文本中提取职业推荐
                # 尝试匹配以###开头的职业名称
                career_matches = regex.findall(r'###\s*(.*?)\s*', response_content)
                logger.info(f"Found career matches: {career_matches}")
                
                # 构建推荐列表
                for i, career in enumerate(career_matches[:3]):
                    career_name = career.strip()
                    if career_name:
                        # 计算匹配度
                        match_score = 90 - i*10
                        processed_recommendations.append({
                            "career": career_name,
                            "matchScore": match_score,
                            "reason": "基于您的背景和技能推荐",
                            "skillsMatch": [],
                            "missingSkills": [],
                            "improvement": ""
                        })
                
                logger.info(f"Extracted {len(processed_recommendations)} recommendations from text after error")
            except Exception as parse_error:
                logger.error(f"Error parsing recommendations from text: {str(parse_error)}")
                # 如果解析失败，使用默认推荐
                processed_recommendations = []
        
        # 确保推荐列表中没有重复的职业
        seen_careers = set()
        unique_recommendations = []
        for rec in processed_recommendations:
            career = rec.get('career', '').strip()
            if career and career not in seen_careers:
                seen_careers.add(career)
                unique_recommendations.append(rec)
        
        # 确保至少返回三个推荐
        if len(unique_recommendations) < 3:
            logger.warning(f"Only found {len(unique_recommendations)} recommendations, using fallback data")
            # 如果没有成功解析出任何推荐或者推荐数量不足，才使用默认推荐
            fallback_recommendations = [
                {
                    "career": "算法工程师",
                    "matchScore": 90,
                    "reason": "基于您的技能和兴趣，算法工程师是一个很好的选择。",
                    "skillsMatch": [],
                    "missingSkills": [],
                    "improvement": ""
                },
                {
                    "career": "机器学习工程师",
                    "matchScore": 80,
                    "reason": "机器学习工程师也是一个与您技能匹配的职业选择。",
                    "skillsMatch": [],
                    "missingSkills": [],
                    "improvement": ""
                },
                {
                    "career": "数据科学家",
                    "matchScore": 70,
                    "reason": "数据科学家是另一个适合您技能背景的职业方向。",
                    "skillsMatch": [],
                    "missingSkills": [],
                    "improvement": ""
                }
            ]
            
            for fallback in fallback_recommendations:
                if len(unique_recommendations) >= 3:
                    break
                career = fallback.get('career')
                if career not in seen_careers:
                    seen_careers.add(career)
                    unique_recommendations.append(fallback)
        
        # 确保最终只有三个推荐
        processed_recommendations = unique_recommendations[:3]
        logger.info(f"Final recommendations: {[rec.get('career') for rec in processed_recommendations]}")
        parse_end = time.time()
        logger.info(f"Recommendation parsing took {parse_end - parse_start:.2f} seconds")
        
        # 保存推荐记录到数据库
        db_start = time.time()
        record, created = CareerRecommendationRecord.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': user,
                'self_introduction': self_introduction,
                'recommendations': processed_recommendations,
                'analysis_result': response_content
            }
        )
        
        if not created:
            record.user = user
            record.self_introduction = self_introduction
            record.recommendations = processed_recommendations
            record.analysis_result = response_content
            record.save()
        
        # 将记录添加到LanceDB
        add_to_lancedb(record)
        
        # 保存统一使用记录
        try:
            AIUsageRecord.objects.create(
                user=user,
                usage_type='recommendation',
                related_id=session_id
            )
        except Exception as e:
            logger.error(f"Error creating AIUsageRecord: {str(e)}")
        db_end = time.time()
        logger.info(f"Database operations took {db_end - db_start:.2f} seconds")
        
        # 计算总响应时间
        total_time = time.time() - start_time
        logger.info(f"Career recommendation completed in {total_time:.2f} seconds: session_id={session_id}, user={user.username if user else 'anonymous'}")
        
        return JsonResponse({
            "success": True,
            "recommendations": processed_recommendations,
            "raw_analysis": response_content,
            "session_id": session_id,
            "response_time": total_time
        })
        
    except Exception as e:
        # 计算总响应时间
        total_time = time.time() - start_time
        logger.error(f"Error in career_recommendation in {total_time:.2f} seconds: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e),
            "response_time": total_time
        }, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def career_plan_generation(request):
    """生成个性化职业规划API接口"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        self_introduction = data.get('self_introduction', '')
        selected_careers = data.get('selected_careers', [])
        
        if not selected_careers:
            return JsonResponse({'error': 'selected_careers is required'}, status=400)
            
        careers_str = "、".join(selected_careers)
        
        # 从数据库获取职业规划提示词，如果没有专门的plan提示词，先使用career
        from ai_integration.langgraph.utils.prompt_manager import get_prompt
        # 可以考虑在PromptManager中添加专门的 'plan_generation'
        plan_prompt = get_prompt('career') 
        
        # 强制要求 JSON 格式输出
        enhanced_prompt = f"""
用户自我介绍：{self_introduction}
用户选择的职业方向：{careers_str}

你的任务是为用户生成一份个性化的职业生涯规划报告，必须且只能输出合法的 JSON 格式数据。不要输出任何其他文本、markdown 标记或解释。

JSON 数据结构要求如下：
{{
  "careerPlan": [
    {{
      "title": "短期职业目标（1-2年）",
      "description": "简要描述短期内的核心目标和发展定位...",
      "details": ["具体行动项1", "具体行动项2", "具体行动项3"]
    }},
    {{
      "title": "中期职业目标（3-5年）",
      "description": "简要描述中期内的核心目标和发展定位...",
      "details": ["具体行动项1", "具体行动项2", "具体行动项3"]
    }},
    {{
      "title": "长期职业目标（5-10年）",
      "description": "简要描述长期内的核心目标和发展定位...",
      "details": ["具体行动项1", "具体行动项2", "具体行动项3"]
    }}
  ],
  "radarData": [
    {{"name": "专业技能", "value": 85}},
    {{"name": "项目经验", "value": 75}},
    {{"name": "团队协作", "value": 90}},
    {{"name": "学习能力", "value": 95}},
    {{"name": "沟通表达", "value": 80}},
    {{"name": "问题解决", "value": 88}}
  ],
  "actionPlan": [
    "具体行动计划步骤1",
    "具体行动计划步骤2",
    "具体行动计划步骤3"
  ]
}}

请根据用户的背景和选择的职业，真实地分析并填充上述 JSON 结构中的各项内容。雷达图(radarData)的六个维度可以根据用户自我介绍智能评估打分（0-100）。
"""
        
        # 创建工作流并执行 (复用 career 模式节点)
        chat_workflow = create_chat_workflow()
        state = {
            "message": enhanced_prompt,
            "mode": "career"
        }
        
        logger.info("Invoking LangGraph workflow for career plan generation")
        result = chat_workflow.invoke(state)
        
        response_content = result.get("response", "")
        
        # 清洗并解析 JSON
        try:
            # 尝试提取 JSON 块
            json_match = regex.search(r'```json\s*([\s\S]*?)\s*```', response_content)
            if json_match:
                clean_content = json_match.group(1).strip()
            else:
                start_idx = response_content.find('{')
                end_idx = response_content.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    clean_content = response_content[start_idx:end_idx+1].strip()
                else:
                    clean_content = response_content.strip()
            
            clean_content = clean_content.replace('{{', '{').replace('}}', '}')
            parsed_content = json.loads(clean_content, strict=False)
            
            return JsonResponse({
                "success": True,
                "data": parsed_content
            })
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse generated career plan JSON: {str(e)}")
            logger.error(f"Raw output: {response_content}")
            return JsonResponse({
                "success": False,
                "error": "解析大模型生成的规划数据失败"
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error in career_plan_generation: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def save_career_recommendation(request):
    """保存职业推荐记录的API接口"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        session_id = data.get('session_id', '')
        self_introduction = data.get('self_introduction', '')
        recommendations = data.get('recommendations', [])
        
        if not session_id:
            return JsonResponse({'error': 'session_id is required'}, status=400)
        
        user = None
        logger.info(f"Request user: {request.user}")
        logger.info(f"Request auth: {request.auth}")
        logger.info(f"Is authenticated: {request.user.is_authenticated}")
        if request.user.is_authenticated:
            user = request.user
        
        record, created = CareerRecommendationRecord.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': user,
                'self_introduction': self_introduction,
                'recommendations': recommendations
            }
        )
        
        if not created:
            record.user = user
            record.self_introduction = self_introduction
            record.recommendations = recommendations
            record.save()
        
        # 将记录添加到LanceDB
        add_to_lancedb(record)
        
        # 保存统一使用记录
        try:
            AIUsageRecord.objects.create(
                user=user,
                usage_type='recommendation',
                related_id=session_id
            )
        except Exception as e:
            logger.error(f"Error creating AIUsageRecord: {str(e)}")
        
        logger.info(f"Career recommendation saved: session_id={session_id}, user={user.username if user else 'anonymous'}")
        
        return JsonResponse({'success': True, 'record_id': record.id})
    
    except Exception as e:
        logger.error(f"Error in save_career_recommendation: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def save_career_plan(request):
    """保存职业生涯规划报告的API接口"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        session_id = data.get('session_id', '')
        report_content = data.get('report_content', '')
        radar_data = data.get('radar_data', {})
        
        if not session_id:
            return JsonResponse({'error': 'session_id is required'}, status=400)
        
        user = None
        logger.info(f"Request user: {request.user}")
        logger.info(f"Request auth: {request.auth}")
        logger.info(f"Is authenticated: {request.user.is_authenticated}")
        if request.user.is_authenticated:
            user = request.user
        
        report, created = CareerPlanReport.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': user,
                'report_content': report_content,
                'radar_data': radar_data
            }
        )
        
        if not created:
            report.user = user
            report.report_content = report_content
            report.radar_data = radar_data
            report.save()
        
        # 保存统一使用记录
        try:
            AIUsageRecord.objects.create(
                user=user,
                usage_type='plan',
                related_id=session_id
            )
        except Exception as e:
            logger.error(f"Error creating AIUsageRecord: {str(e)}")
        
        logger.info(f"Career plan report saved: session_id={session_id}, user={user.username if user else 'anonymous'}")
        
        return JsonResponse({'success': True, 'report_id': report.id})
    
    except Exception as e:
        logger.error(f"Error in save_career_plan: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_user_ai_records(request):
    """获取用户的AI使用记录"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # 获取用户的所有AI使用记录
        usage_records = AIUsageRecord.objects.filter(user=request.user).order_by('-created_at')
        
        # 构建响应数据
        records = []
        for record in usage_records:
            records.append({
                'id': record.id,
                'usage_type': record.usage_type,
                'related_id': record.related_id,
                'created_at': record.created_at.isoformat(),
                'tags': [tag.name for tag in record.tags.all()]
            })
        
        return JsonResponse({'success': True, 'records': records})
    
    except Exception as e:
        logger.error(f"Error in get_user_ai_records: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_chat_records(request):
    """获取用户的聊天记录"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # 获取用户的所有聊天会话
        conversations = AIConversation.objects.filter(user=request.user).order_by('-created_at')
        
        # 构建响应数据
        records = []
        for conversation in conversations:
            # 使用新的AIChatPair模型获取聊天记录
            chat_pairs = AIChatPair.objects.filter(conversation=conversation).order_by('input_time')
            
            message_pairs = []
            for pair in chat_pairs:
                # 处理None值
                output = pair.ai_output
                user_input = pair.user_input
                
                # 检测工具调用失败的情况
                if output and 'NoneNoneNoneNone' in output:
                    # 重新生成时间回答
                    current_time = get_time()
                    output = f"当前时间是：{current_time}"
                
                message_pairs.append({
                    'input': user_input,
                    'input_time': pair.input_time.isoformat(),
                    'output': output,
                    'output_time': pair.output_time.isoformat() if pair.output_time else None
                })
            
            records.append({
                'id': conversation.id,
                'session_id': conversation.session_id,
                'mode': conversation.mode,
                'created_at': conversation.created_at.isoformat(),
                'username': request.user.username,
                'message_pairs': message_pairs,
                'tags': [tag.name for tag in conversation.tags.all()]
            })
        
        return JsonResponse({'success': True, 'conversations': records})
    
    except Exception as e:
        logger.error(f"Error in get_chat_records: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_evaluation_records(request):
    """获取用户的职业评测记录"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # 获取用户的所有职业评测记录
        records = CareerEvaluationRecord.objects.filter(user=request.user).order_by('-created_at')
        
        # 构建响应数据
        evaluation_records = []
        for record in records:
            evaluation_records.append({
                'session_id': record.session_id,
                'selected_careers': record.selected_careers,
                'evaluation_result': record.evaluation_result,
                'created_at': record.created_at.isoformat(),
                'tags': [tag.name for tag in record.tags.all()]
            })
        
        return JsonResponse({'success': True, 'records': evaluation_records})
    
    except Exception as e:
        logger.error(f"Error in get_evaluation_records: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_plan_reports(request):
    """获取用户的职业生涯规划报告"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # 获取用户的所有职业生涯规划报告
        reports = CareerPlanReport.objects.filter(user=request.user).order_by('-created_at')
        
        # 构建响应数据
        plan_reports = []
        for report in reports:
            plan_reports.append({
                'session_id': report.session_id,
                'report_content': report.report_content,
                'radar_data': report.radar_data,
                'created_at': report.created_at.isoformat(),
                'tags': [tag.name for tag in report.tags.all()]
            })
        
        return JsonResponse({'success': True, 'reports': plan_reports})
    
    except Exception as e:
        logger.error(f"Error in get_plan_reports: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def add_tag_to_record(request):
    """为AI使用记录添加标签"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        record_id = data.get('record_id')
        record_type = data.get('record_type')  # 'chat', 'evaluation', 'plan'
        tag_name = data.get('tag_name')
        
        if not record_id or not record_type or not tag_name:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # 获取或创建标签
        tag, created = AITag.objects.get_or_create(name=tag_name)
        
        # 根据记录类型添加标签
        if record_type == 'chat':
            try:
                conversation = AIConversation.objects.get(id=record_id, user=request.user)
                conversation.tags.add(tag)
            except AIConversation.DoesNotExist:
                return JsonResponse({'error': 'Conversation not found'}, status=404)
        elif record_type == 'evaluation':
            try:
                record = CareerEvaluationRecord.objects.get(id=record_id, user=request.user)
                record.tags.add(tag)
            except CareerEvaluationRecord.DoesNotExist:
                return JsonResponse({'error': 'Evaluation record not found'}, status=404)
        elif record_type == 'plan':
            try:
                report = CareerPlanReport.objects.get(id=record_id, user=request.user)
                report.tags.add(tag)
            except CareerPlanReport.DoesNotExist:
                return JsonResponse({'error': 'Plan report not found'}, status=404)
        else:
            return JsonResponse({'error': 'Invalid record type'}, status=400)
        
        return JsonResponse({'success': True, 'tag_id': tag.id})
    
    except Exception as e:
        logger.error(f"Error in add_tag_to_record: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_record(request):
    """删除AI使用记录"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        record_id = data.get('record_id')
        record_type = data.get('record_type')  # 'chat', 'evaluation', 'plan'
        
        if not record_id or not record_type:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # 根据记录类型删除
        if record_type == 'chat':
            try:
                conversation = AIConversation.objects.get(id=record_id, user=request.user)
                conversation.delete()
            except AIConversation.DoesNotExist:
                return JsonResponse({'error': 'Conversation not found'}, status=404)
        elif record_type == 'evaluation':
            try:
                record = CareerEvaluationRecord.objects.get(id=record_id, user=request.user)
                record.delete()
            except CareerEvaluationRecord.DoesNotExist:
                return JsonResponse({'error': 'Evaluation record not found'}, status=404)
        elif record_type == 'plan':
            try:
                report = CareerPlanReport.objects.get(id=record_id, user=request.user)
                report.delete()
            except CareerPlanReport.DoesNotExist:
                return JsonResponse({'error': 'Plan report not found'}, status=404)
        else:
            return JsonResponse({'error': 'Invalid record type'}, status=400)
        
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Error in delete_record: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_chat_history(request):
    """获取对话历史（短期记忆）"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        session_id = request.query_params.get('session_id')
        limit = request.query_params.get('limit', 10)
        
        if not session_id:
            return JsonResponse({'error': 'session_id is required'}, status=400)
        
        # 获取对话
        conversation = AIConversation.objects.filter(session_id=session_id).first()
        if not conversation:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        
        # 检查权限
        if conversation.user and request.user.is_authenticated and conversation.user != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # 获取对话历史
        chat_pairs = AIChatPair.objects.filter(conversation=conversation).order_by('input_time')[:int(limit)]
        
        # 构建响应
        chat_history = []
        for pair in chat_pairs:
            chat_history.append({
                'id': pair.id,
                'user_input': pair.user_input,
                'ai_output': pair.ai_output,
                'input_time': pair.input_time.isoformat(),
                'output_time': pair.output_time.isoformat() if pair.output_time else None
            })
        
        return JsonResponse({
            'success': True,
            'chat_history': chat_history,
            'session_id': session_id,
            'mode': conversation.mode
        })
    except Exception as e:
        logger.error(f"Error in get_chat_history: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_long_term_memory(request):
    """获取长期记忆"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        categories = request.query_params.getlist('categories')
        limit = request.query_params.get('limit', 10)
        
        # 获取长期记忆
        user = request.user if request.user.is_authenticated else None
        memories = memory_agent.get_long_term_memory(user=user, categories=categories, limit=int(limit))
        
        return JsonResponse({
            'success': True,
            'memories': memories
        })
    except Exception as e:
        logger.error(f"Error in get_long_term_memory: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_memory(request):
    """更新长期记忆"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        memory_id = data.get('memory_id')
        new_value = data.get('value')
        
        if not memory_id or not new_value:
            return JsonResponse({'error': 'memory_id and value are required'}, status=400)
        
        # 更新记忆
        success = memory_agent.update_memory(memory_id, new_value)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Failed to update memory'}, status=404)
    except Exception as e:
        logger.error(f"Error in update_memory: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_memory(request):
    """删除长期记忆"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        memory_id = data.get('memory_id')
        
        if not memory_id:
            return JsonResponse({'error': 'memory_id is required'}, status=400)
        
        # 删除记忆
        success = memory_agent.delete_memory(memory_id)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Failed to delete memory'}, status=404)
    except Exception as e:
        logger.error(f"Error in delete_memory: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_user_interview_reviews(request):
    """
    获取用户的面试复盘记录列表
    
    Returns:
        包含复盘会话信息和最近问答内容的列表
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({"success": False, "error": "未登录"}, status=401)
        
        # 查询用户的复盘记录
        review_records = InterviewReviewRecord.objects.filter(
            user=user
        ).order_by('-created_at')[:10]
        
        result = []
        for record in review_records:
            result.append({
                'id': record.id,
                'session_id': record.conversation.session_id if record.conversation else '',
                'interview_style': record.interview_style,
                'overall_score': record.overall_score,
                'interview_duration': record.interview_duration,
                'pair_count': record.question_count,  # 前端期望的字段名
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M'),
                'latest_content': record.review_content[:150] + '...' if record.review_content else '无内容'  # 前端期望的字段名
            })
        
        return JsonResponse({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"获取面试复盘失败: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_interview_review_detail(request, session_id):
    """
    获取单个面试复盘记录的详细内容
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({"success": False, "error": "未登录"}, status=401)
        
        # 先查找关联的会话
        conversation = None
        try:
            conversation = AIConversation.objects.get(session_id=session_id)
        except AIConversation.DoesNotExist:
            pass
        
        # 查询复盘记录
        review_record = None
        if conversation:
            review_record = InterviewReviewRecord.objects.filter(
                user=user,
                conversation=conversation
            ).first()
        
        if not review_record:
            # 如果通过会话找不到，尝试通过session_id直接查找
            review_record = InterviewReviewRecord.objects.filter(
                user=user,
                conversation__session_id=session_id
            ).first()
        
        if not review_record:
            return JsonResponse({
                "success": False,
                "error": "未找到复盘记录"
            }, status=404)
        
        return JsonResponse({
            "success": True,
            "data": {
                'id': review_record.id,
                'session_id': session_id,
                'interview_style': review_record.interview_style,
                'overall_score': review_record.overall_score,
                'interview_duration': review_record.interview_duration,
                'question_count': review_record.question_count,
                'answer_count': review_record.answer_count,
                'review_content': review_record.review_content,
                'strengths': review_record.strengths,
                'weaknesses': review_record.weaknesses,
                'suggestions': review_record.suggestions,
                'created_at': review_record.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
    except Exception as e:
        logger.error(f"获取复盘详情失败: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def save_interview_review(request):
    """
    保存面试复盘记录到数据库
    
    请求参数:
        session_id: 面试会话ID
        review_content: 复盘报告内容
        interview_style: 面试风格
        interview_duration: 面试时长(分钟)
        question_count: 问题数量
        answer_count: 回答数量
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        session_id = data.get('session_id', '')
        review_content = data.get('review_content', '')
        interview_style = data.get('interview_style', 'gentle')
        interview_duration = data.get('interview_duration', 0)
        question_count = data.get('question_count', 0)
        answer_count = data.get('answer_count', 0)
        
        logger.info(f"[REVIEW] 收到保存复盘请求 - session_id: {session_id[:20]}..., authenticated: {request.user.is_authenticated}, user: {request.user}")
        
        if not session_id:
            return JsonResponse({'error': 'session_id is required'}, status=400)
        
        user = None
        if request.user.is_authenticated:
            user = request.user
            logger.info(f"[REVIEW] 用户已认证: {user.username} (ID: {user.id})")
        
        # 查找关联的会话
        conversation = None
        try:
            conversation = AIConversation.objects.get(session_id=session_id)
            logger.info(f"[REVIEW] 找到关联会话: {conversation.id}")
        except AIConversation.DoesNotExist:
            logger.warning(f"[REVIEW] 未找到关联会话: {session_id}")
        
        from ai_integration.interview import get_interview_service
        parsed_review = get_interview_service().parse_review(review_content)

        # 创建复盘记录
        review_record = InterviewReviewRecord.objects.create(
            user=user,
            conversation=conversation,
            interview_style=interview_style,
            interview_duration=interview_duration,
            review_content=review_content,
            strengths=parsed_review['strengths'],
            weaknesses=parsed_review['weaknesses'],
            suggestions=parsed_review['suggestions'],
            overall_score=parsed_review['overall_score'],
            question_count=question_count,
            answer_count=answer_count
        )
        
        logger.info(f"面试复盘记录已保存: {review_record.id}")
        
        return JsonResponse({
            "success": True,
            "message": "复盘记录保存成功",
            "review_id": review_record.id
        })
    except Exception as e:
        logger.error(f"保存面试复盘失败: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)
