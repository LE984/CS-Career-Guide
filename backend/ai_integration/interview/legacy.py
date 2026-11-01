"""Existing prompt-driven implementation; preserve its prompts and text parsing."""

import re

from .service import InterviewPrompt


class LegacyPromptInterview:
    def __init__(self, prompt_loader):
        self.prompt_loader = prompt_loader

    def prepare_turn(self, message, history, style, *, review=False):
        context = ''
        if review:
            review_prompt = self.prompt_loader('review')
            if review_prompt:
                context = review_prompt + '\n\n'
        if history:
            context += '对话历史：\n'
            for item in history:
                if item['user']:
                    context += f"用户：{item['user']}\n"
                if item['ai']:
                    context += f"面试官：{item['ai']}\n"
        prompt = context + message
        if len(prompt) > 3000:
            prompt = prompt[:3000] + '...'
        if review:
            # Compatibility: the original review path used chat as its system
            # prompt, with the review instruction prepended to the user text.
            system = self.prompt_loader('chat')
        else:
            styles = {
                'pressure': '对面试人员使用及其压迫的提问方式，要求候选人在短时间内给出回答。',
                'technical': '极致理性的硬核技术深挖，针对底层原理进行连环追问。',
                'behavioral': '关注过往经历中的决策、冲突处理及团队协作等软技能。',
            }
            description = styles.get(style, '语气友好亲切，侧重引导与交流，适合舒缓紧张感。')
            system = self.prompt_loader('interview') + '\n\n风格：' + description
        system += ('\n\n输出要求：只输出纯文本，不使用 Markdown 标记、代码围栏、表格、标题符号或星号。'
                   '代码和技术名词用普通文本表达。复盘使用中文段落标题和换行，'
                   '保留“回答的优点：”“需要改进的地方：”“具体改进建议：”“综合评分：”等字段。')
        return InterviewPrompt(system=system, user=prompt)

    def parse_review(self, content):
        return {
            'strengths': extract_section(content, '回答的优点：', '需要改进的地方：'),
            'weaknesses': extract_section(content, '需要改进的地方：', '具体改进建议：'),
            'suggestions': extract_section(content, '具体改进建议：', '下次面试'),
            'overall_score': extract_score(content),
        }


def extract_section(content, start_marker, end_marker):
    if not content:
        return None
    start = content.find(start_marker)
    if start == -1:
        return None
    start += len(start_marker)
    end = content.find(end_marker, start)
    section = content[start:] if end == -1 else content[start:end]
    lines = []
    for line in section.strip().split('\n'):
        cleaned = re.sub(r'^\s*(\d+\.|（\d+）|\d+\s*、)\s*', '', line).strip()
        if cleaned and cleaned not in ('：', ':'):
            lines.append(cleaned)
    return '\n'.join(lines)


def extract_score(content):
    if not content:
        return None
    for pattern in (
        r'综合评分[：:]?\s*(\d+\.?\d*)', r'得分[：:]?\s*(\d+\.?\d*)',
        r'评分[：:]?\s*(\d+\.?\d*)', r'(\d+\.?\d*)\s*分',
    ):
        match = re.search(pattern, content)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None
