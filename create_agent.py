from llama_index.core.agent import ReActAgent
from llama_index.llms.openai import OpenAI
from constants import LLMConfig, AgentConfig, OpenAIConfig
import os
from llama_index.core.prompts import PromptTemplate
from llama_index.core.memory import ChatMemoryBuffer
from dotenv import load_dotenv
from sql_tester import tool
from sarvam_tool import SarvamTranslatorToolSpec
from openai import AsyncOpenAI
load_dotenv()  

api_key = os.getenv("OPENAI_API_KEY")
API_KEY_ENV_VAR = os.getenv("SARVAM_API_KEY")

def create_agent():
    with open("db_schema_prompt.txt", "r", encoding="utf-8") as f:
        prompt_text = f.read()

    memory = ChatMemoryBuffer.from_defaults(token_limit=1000)   
    system_prompt = PromptTemplate(prompt_text)

    sarvamLLM = AsyncOpenAI(                  
        api_key=API_KEY_ENV_VAR, 
        base_url=LLMConfig.API_BASE,          
        timeout=LLMConfig.TIMEOUT,            
    )

    llm = OpenAI(
        api_key=api_key,
        api_base="https://api.openai.com/v1",  
        model="o4-mini",
        timeout=240,
        strict_validation=False,
    )

    tools = tool.to_tool_list()
    translator_spec = SarvamTranslatorToolSpec(sarvamLLM)
    tools += translator_spec.to_tool_list()  

    return ReActAgent.from_tools(
        tools,
        llm=llm,
        verbose=AgentConfig.VERBOSE,
        system_prompt=system_prompt,
        memory=memory,
        max_iterations = 25
    )
