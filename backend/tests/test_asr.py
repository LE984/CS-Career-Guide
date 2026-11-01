"""Exercise ASR wire events with fake sockets; no credentials or network."""

import ast
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock
import uuid


def event(name, output=None):
    return json.dumps({'header': {'event': name}, 'payload': {'output': output or {}}})


class Socket:
    def __init__(self, messages):
        self.messages = iter(messages)
        self.send = AsyncMock()

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.messages)
        except StopIteration:
            raise StopAsyncIteration

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class ASRTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / 'asr/asr.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        self.settings = SimpleNamespace(ASR_API_KEY='fake-key', ASR_WSS_URL='wss://asr.invalid',
                                        ASR_MODEL='fun-asr-realtime')
        self.websockets = SimpleNamespace(connect=Mock())
        self.namespace = {'asyncio': asyncio, 'json': json, 'uuid': uuid,
                          'APIView': object, 'IsAuthenticated': object,
                          'settings': self.settings, 'websockets': self.websockets,
                          'Response': lambda data, status=200: (status, data)}
        exec(compile(ast.Module(body=classes, type_ignores=[]), str(path), 'exec'), self.namespace)
        self.view = self.namespace['ASRView']()
        self.error = self.namespace['ASRServiceError']

    async def test_fun_asr_final_sentences_and_heartbeat(self):
        ws = Socket([event('result-generated', {'sentence': {'text': '中间', 'sentence_end': False}}),
                     event('result-generated', {'sentence': {'text': '你好', 'sentence_end': True}}),
                     event('result-generated', {'sentence': {'text': '心跳', 'sentence_end': True, 'heartbeat': True}}),
                     event('result-generated', {'sentence': {'text': '世界', 'sentence_end': True}}),
                     event('task-finished')])
        self.assertEqual(await self.view.asr_receiver(ws), '你好世界')

    async def test_legacy_gummy_response_remains_supported(self):
        ws = Socket([event('result-generated', {'transcription': {'text': '旧协议', 'sentence_end': True}}),
                     event('task-finished')])
        self.assertEqual(await self.view.asr_receiver(ws), '旧协议')

    async def test_provider_failure_is_not_empty_success(self):
        with self.assertRaises(self.error):
            await self.view.asr_receiver(Socket([event('task-failed')]))

    async def test_connection_must_finish_explicitly(self):
        with self.assertRaises(self.error):
            await self.view.asr_receiver(Socket([]))

    async def test_fun_asr_start_and_finish_commands(self):
        ws = Socket([event('task-started'), event('task-finished')])
        self.websockets.connect.return_value = ws
        self.assertEqual(await self.view.run_asr_tasks(b'\0\0'), '')
        sent = [call.args[0] for call in ws.send.call_args_list]
        start, finish = json.loads(sent[0]), json.loads(sent[-1])
        self.assertEqual(start['payload']['parameters'], {'format': 'pcm', 'sample_rate': 16000})
        self.assertEqual(start['payload']['model'], 'fun-asr-realtime')
        self.assertEqual(sent[1], b'\0\0')
        self.assertEqual(finish['header']['action'], 'finish-task')
        self.assertEqual(start['header']['task_id'], finish['header']['task_id'])

    async def test_legacy_start_keeps_transcription_enabled(self):
        self.settings.ASR_MODEL = 'gummy-realtime-v1'
        ws = Socket([event('task-started'), event('task-finished')])
        self.websockets.connect.return_value = ws
        await self.view.run_asr_tasks(b'')
        self.assertTrue(json.loads(ws.send.call_args_list[0].args[0])['payload']['parameters']['transcription_enabled'])

    async def test_start_failure_does_not_send_audio(self):
        ws = Socket([event('task-failed')])
        self.websockets.connect.return_value = ws
        with self.assertRaises(self.error):
            await self.view.run_asr_tasks(b'audio')
        self.assertEqual(ws.send.call_count, 1)

    async def test_start_close_does_not_send_audio(self):
        self.websockets.connect.return_value = Socket([])
        with self.assertRaises(self.error):
            await self.view.run_asr_tasks(b'audio')

    async def test_failed_receiver_cancels_sender(self):
        self.websockets.connect.return_value = Socket([event('task-started'), event('task-failed')])
        cancelled = asyncio.Event()

        async def slow_sender(*args):
            try:
                await asyncio.Future()
            finally:
                cancelled.set()

        self.view.asr_sender = slow_sender
        with self.assertRaises(ExceptionGroup):
            await self.view.run_asr_tasks(b'audio')
        self.assertTrue(cancelled.is_set())


class ASRResponseTests(unittest.TestCase):
    def setUp(self):
        harness = ASRTests()
        harness.setUp()
        self.view = harness.view
        self.request = SimpleNamespace(FILES={'audio': SimpleNamespace(read=lambda: b'audio')})

    def test_provider_errors_are_redacted(self):
        self.view.run_asr_tasks = AsyncMock(side_effect=RuntimeError('secret-key-provider-response'))
        status, body = self.view.post(self.request)
        self.assertEqual(status, 502)
        self.assertNotIn('secret-key', json.dumps(body))

    def test_timeout_is_distinct(self):
        self.view.run_asr_tasks = AsyncMock(side_effect=TimeoutError)
        self.assertEqual(self.view.post(self.request)[0], 504)

    def test_missing_audio_is_bad_request(self):
        self.assertEqual(self.view.post(SimpleNamespace(FILES={}))[0], 400)
