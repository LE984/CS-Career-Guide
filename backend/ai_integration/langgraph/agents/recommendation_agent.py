from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from ..tools.time_tool import get_time
from ..tools import keyword_search_tool, semantic_search_tool, read_chunk_tool
from ..utils.prompt_manager import get_prompt
from cs_career_guide.ai_config import get_llm_kwargs
import logging

logger = logging.getLogger(__name__)

def create_recommendation_agent():
    """创建推荐代理"""
    try:
        llm = ChatOpenAI(
            temperature=0.7,
            **get_llm_kwargs(),
        )
        
        tools = [
            keyword_search_tool,
            semantic_search_tool,
            read_chunk_tool,
            get_time
        ]
        
        llm_with_tools = llm.bind_tools(tools)
        
        system_prompt = get_prompt('recommendation')
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{messages}")
        ])
        
        agent_chain = prompt | llm_with_tools
        
        return agent_chain
        
    except Exception as e:
        logger.error(f"Error creating recommendation agent: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise
