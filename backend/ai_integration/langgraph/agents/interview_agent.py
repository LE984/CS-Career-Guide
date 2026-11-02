from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from ..tools.time_tool import get_time
from ..utils.prompt_manager import get_prompt
from cs_career_guide.ai_config import get_llm_kwargs

def create_interview_agent():
    llm = ChatOpenAI(
        temperature=0.7,
        **get_llm_kwargs(),
    )
    
    # 创建工具列表
    tools = []
    
    # 绑定工具到LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # 从数据库获取提示词
    system_prompt = get_prompt('interview')
    
    # 创建提示模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{messages}")
    ])
    
    # 创建代理链
    agent_chain = prompt | llm_with_tools
    
    return agent_chain
