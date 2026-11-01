"""Characterize legacy interview behavior without Django setup, DB or model I/O."""

import ast
import asyncio
from datetime import datetime
import json
from pathlib import Path
from queue import Queue
import sys
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_integration.interview.legacy import LegacyPromptInterview
from ai_integration.interview.service import InterviewPrompt, InterviewService


class InterviewBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.prompts = {'interview': '面试系统', 'review': '复盘要求', 'chat': '聊天系统'}
        self.service = InterviewService(LegacyPromptInterview(self.prompts.get))

    def test_turn_preserves_history_order_style_and_prompt_limit(self):
        history = [{'user': '问题一', 'ai': '回答一'}, {'user': '', 'ai': '回答二'}]
        turn = self.service.prepare_turn('本轮回答', history, 'technical')
        self.assertEqual(turn.user, '对话历史：\n用户：问题一\n面试官：回答一\n面试官：回答二\n本轮回答')
        self.assertTrue(turn.system.startswith('面试系统\n\n风格：极致理性的硬核技术深挖，针对底层原理进行连环追问。'))
        self.assertIn('只输出纯文本，不使用 Markdown', turn.system)
        self.assertEqual(self.service.prepare_turn('字' * 3001, [], 'gentle').user, '字' * 3000 + '...')
        self.assertIn('对面试人员使用及其压迫的提问方式，要求候选人在短时间内给出回答。', self.service.prepare_turn('回答', [], 'pressure').system)
        self.assertIn('关注过往经历中的决策、冲突处理及团队协作等软技能。', self.service.prepare_turn('回答', [], 'behavioral').system)
        self.assertEqual(self.service.prepare_turn('回答', [], 'unknown'), self.service.prepare_turn('回答', [], 'gentle'))

    def test_review_retains_legacy_chat_system_and_review_user_prefix(self):
        turn = self.service.prepare_turn('本次对话', [], 'pressure', review=True)
        self.assertTrue(turn.system.startswith('聊天系统\n\n输出要求：'))
        self.assertIn('只输出纯文本', turn.system)
        self.assertEqual(turn.user, '复盘要求\n\n本次对话')

    def test_review_parsing_keeps_existing_markers_and_missing_values(self):
        content = '回答的优点：\n1. 清晰\n（2）具体\n需要改进的地方：\n1、举例不足\n具体改进建议：\n补充证据\n下次面试准备\n综合评分：82.5'
        self.assertEqual(self.service.parse_review(content), {
            'strengths': '清晰\n具体', 'weaknesses': '举例不足',
            'suggestions': '补充证据', 'overall_score': 82.5,
        })
        self.assertEqual(self.service.parse_review('无结构的复盘'), {
            'strengths': None, 'weaknesses': None, 'suggestions': None, 'overall_score': None,
        })

    def test_replacement_strategy_needs_no_http_or_orm_dependencies(self):
        replacement = Mock()
        replacement.prepare_turn.return_value = InterviewPrompt('new system', 'new question')
        service = InterviewService(replacement)
        self.assertEqual(service.prepare_turn('answer', [], 'gentle').user, 'new question')
        replacement.prepare_turn.assert_called_once_with('answer', [], 'gentle', review=False)
        service.parse_review('new report')
        replacement.parse_review.assert_called_once_with('new report')


class ChatRouteIntegrationTests(unittest.TestCase):
    def test_review_save_uses_selected_parser_and_keeps_existing_record_fields(self):
        source = Path(__file__).resolve().parents[1] / 'ai_integration/langgraph_views.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        view = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'save_interview_review')
        conversation = SimpleNamespace(id=7)
        conversations, reviews = Mock(), Mock()
        conversations.get.return_value = conversation
        reviews.create.return_value = SimpleNamespace(id=9)
        service = Mock()
        service.parse_review.return_value = {
            'strengths': 'custom strength', 'weaknesses': 'custom weakness',
            'suggestions': 'custom suggestion', 'overall_score': 88,
        }
        namespace = {
            'api_view': lambda methods: lambda fn: fn,
            'authentication_classes': lambda classes: lambda fn: fn,
            'permission_classes': lambda classes: lambda fn: fn,
            'TokenAuthentication': object, 'IsAuthenticated': object,
            'JsonResponse': lambda data, status=200: {'data': data, 'status': status},
            'json': json, 'logger': Mock(),
            'AIConversation': SimpleNamespace(objects=conversations, DoesNotExist=LookupError),
            'InterviewReviewRecord': SimpleNamespace(objects=reviews),
        }
        exec(compile(ast.Module(body=[view], type_ignores=[]), str(source), 'exec'), namespace)
        user = SimpleNamespace(is_authenticated=True, username='offline', id=1)
        data = {'session_id': 's1', 'review_content': 'report', 'interview_style': 'technical',
                'interview_duration': 3, 'question_count': 2, 'answer_count': 2}
        request = SimpleNamespace(method='POST', user=user, body=json.dumps(data).encode())
        with patch('ai_integration.interview.get_interview_service', return_value=service):
            result = namespace['save_interview_review'](request)
        self.assertEqual(result, {'data': {'success': True, 'message': '复盘记录保存成功', 'review_id': 9}, 'status': 200})
        service.parse_review.assert_called_once_with('report')
        fields = reviews.create.call_args.kwargs
        self.assertIs(fields['user'], user)
        self.assertIs(fields['conversation'], conversation)
        self.assertEqual(fields['strengths'], 'custom strength')
        self.assertEqual(fields['overall_score'], 88)
        self.assertEqual(fields['interview_duration'], 3)
        self.assertEqual(fields['question_count'], 2)

    def test_actual_route_uses_strategy_and_retains_lazy_sse_and_chat_pair(self):
        source = Path(__file__).resolve().parents[1] / 'ai_integration/langgraph_views.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        view = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'llm_chat')
        class Response(dict):
            def __init__(self, stream=None, content_type=None, status=200):
                self.streaming_content = stream
                self.status_code = status
        conversation = SimpleNamespace(context_aware=False)
        conversations = Mock()
        conversations.get_or_create.return_value = (conversation, True)
        pairs, model_factory = Mock(), Mock()
        model_factory.return_value.stream.return_value = [SimpleNamespace(content='下一题')]
        service = Mock()
        service.prepare_turn.return_value = InterviewPrompt('策略系统提示', '策略输入')
        prompt_loader = Mock(return_value='普通聊天提示')
        namespace = {
            'csrf_exempt': lambda fn: fn, 'JsonResponse': Response, 'StreamingHttpResponse': Response,
            'time': time, 'json': json, 'logger': Mock(), 'datetime': datetime,
            'Queue': Queue, 'threading': threading, 'asyncio': asyncio,
            'AIConversation': SimpleNamespace(objects=conversations),
            'AIChatPair': SimpleNamespace(objects=pairs), 'memory_agent': Mock(),
            # Even when enabled on the server, a text-only client must never
            # touch the WebSocket provider (not present in this namespace).
            'settings': SimpleNamespace(ENABLE_TTS=True), 'get_llm_kwargs': lambda: {'model': 'offline'},
            'build_user_profile_prompt': lambda request: '职业背景：',
        }
        exec(compile(ast.Module(body=[view], type_ignores=[]), str(source), 'exec'), namespace)
        modules = {
            'langchain_openai': SimpleNamespace(ChatOpenAI=model_factory),
            'langchain_core.messages': SimpleNamespace(
                SystemMessage=lambda **kwargs: kwargs, HumanMessage=lambda **kwargs: kwargs),
            'ai_integration.langgraph.utils.prompt_manager': SimpleNamespace(get_prompt=prompt_loader),
        }
        for mode, message in (('interview', '回答'), ('pressure_interview', '【面试模式】回答'), ('interview_review', '复盘'), ('normal', '你好'), ('career', '职业问题')):
            with self.subTest(mode=mode), patch.dict(sys.modules, modules), patch('ai_integration.interview.get_interview_service', return_value=service):
                model_factory.reset_mock()
                service.reset_mock()
                request = SimpleNamespace(method='POST', FILES={}, body=json.dumps({
                    'mode': mode, 'message': message, 'session_id': 'offline-session', 'interview_style': 'technical',
                }).encode())
                response = namespace['llm_chat'](request)
                self.assertEqual(response.status_code, 200)
                model_factory.assert_not_called()  # No model invocation before consumption.
                events = list(response.streaming_content)
                self.assertIn('下一题', events[0])
                self.assertIn('data: [DONE]', events[1])
                self.assertIn('"session_id": "offline-session"', events[2])
                if mode in ('normal', 'career'):
                    service.prepare_turn.assert_not_called()
                    model_factory.return_value.stream.assert_called_with([
                        {'content': '普通聊天提示'},
                        {'content': ('职业背景：' if mode == 'career' else '') + message},
                    ])
                else:
                    model_factory.return_value.stream.assert_called_with([
                        {'content': '策略系统提示'}, {'content': '策略输入'},
                    ])
                    service.prepare_turn.assert_called_with(message, [], 'technical', review=mode == 'interview_review')
                self.assertEqual(pairs.create.call_args.kwargs['user_input'], message)
                self.assertEqual(pairs.create.call_args.kwargs['ai_output'], '下一题')


if __name__ == '__main__':
    unittest.main()
