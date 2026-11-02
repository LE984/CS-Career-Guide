import json
import re
from typing import Any, Dict

from langchain_openai import ChatOpenAI
from cs_career_guide.ai_config import get_llm_kwargs


def get_llm(temperature: float = 0.4) -> ChatOpenAI:
    return ChatOpenAI(
        temperature=temperature,
        **get_llm_kwargs("CAREER_REPORT_MODEL"),
    )


def parse_json_response(raw_text: str) -> Dict[str, Any]:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```json\s*([\s\S]*?)\s*```", raw_text)
    if fenced:
        try:
            return json.loads(fenced.group(1).strip())
        except json.JSONDecodeError:
            pass

    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(raw_text[start : end + 1])

    raise ValueError("Model response does not contain valid JSON")
