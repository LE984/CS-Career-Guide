import asyncio
import json
import uuid

import websockets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings


class ASRServiceError(RuntimeError):
    """A provider failed without exposing its response or credentials."""


class ASRView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        audio = request.FILES.get('audio')
        if not audio:
            return Response({
                'result': '音频不存在'
            }, status=400)
        pcm_data = audio.read()
        try:
            text = asyncio.run(self.run_asr_tasks(pcm_data))
        except TimeoutError:
            return Response({'result': '语音识别超时，请重试'}, status=504)
        except Exception:
            # Provider messages may contain account information. Never forward them.
            return Response({'result': '语音识别服务暂不可用，请稍后重试'}, status=502)
        return Response({
            'result': 'success',
            'text': text,
        })

    async def asr_sender(self, pcm_data, ws, task_id):
        chunk = 3200
        for i in range(0, len(pcm_data), chunk):
            await ws.send(pcm_data[i: i + chunk])
            await asyncio.sleep(0.01)
        await ws.send(json.dumps({
            "header": {
                "action": "finish-task",
                "task_id": task_id,
                "streaming": "duplex"
            },
            "payload": {
                "input": {}
            }
        }))

    async def asr_receiver(self, ws):
        text = ''
        async for msg in ws:
            data = json.loads(msg)
            event = data.get('header', {}).get('event')
            if event == 'result-generated':
                output = data.get('payload', {}).get('output', {})
                # Fun-ASR returns sentence; preserve the legacy Gummy response.
                sentence = output.get('sentence') or output.get('transcription') or {}
                if sentence.get('sentence_end') and not sentence.get('heartbeat'):
                    text += sentence.get('text', '')
            elif event == 'task-failed':
                raise ASRServiceError('ASR task failed')
            elif event == 'task-finished':
                return text
        raise ASRServiceError('ASR connection ended before task completion')

    async def run_asr_tasks(self, pcm_data):
        task_id = uuid.uuid4().hex
        api_key = settings.ASR_API_KEY
        wss_url = settings.ASR_WSS_URL
        
        if not api_key:
            raise ValueError("ASR_API_KEY or LLM_API_KEY environment variable not set")
        if not wss_url:
            raise ValueError("ASR_WSS_URL environment variable not set")
        if not settings.ASR_MODEL:
            raise ValueError("ASR_MODEL environment variable not set")
            
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        async with asyncio.timeout(120), websockets.connect(wss_url, additional_headers=headers) as ws:
            parameters = {'sample_rate': 16000, 'format': 'pcm'}
            if not settings.ASR_MODEL.startswith('fun-asr'):
                parameters['transcription_enabled'] = True
            await ws.send(json.dumps({
                "header": {
                    "streaming": "duplex",
                    "task_id": task_id,
                    "action": "run-task"
                },
                "payload": {
                    "model": settings.ASR_MODEL,
                    "parameters": parameters,
                    "input": {},
                    "task": "asr",
                    "task_group": "audio",
                    "function": "recognition"
                }
            }))
            async for msg in ws:
                event = json.loads(msg).get('header', {}).get('event')
                if event == 'task-failed':
                    raise ASRServiceError('ASR task failed to start')
                if event == 'task-started':
                    break
            else:
                raise ASRServiceError('ASR connection ended before task start')
            # Cancel the sender too if the receiver reports an early failure.
            async with asyncio.TaskGroup() as tasks:
                tasks.create_task(self.asr_sender(pcm_data, ws, task_id))
                receiver = tasks.create_task(self.asr_receiver(ws))
            return receiver.result()
